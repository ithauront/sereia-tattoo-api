from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application.studio.use_cases.DTO.payment_dto import CreatePaymentInput
from app.application.studio.use_cases.finances_use_cases.create_payment_use_case import (
    CreatePaymentUseCase,
)
from app.core.exceptions.appointments import (
    AppointmentClientInfoBreakingDomainRules,
    AppointmentNotFoundError,
    IncorrectAppointmentStatusError,
)
from app.core.exceptions.payment import (
    DuplicateExternalReferenceError,
    IdempotencyKeyConflictError,
    PaymentConsumesZeroClientCreditsError,
    PaymentMustBeGreaterThanZeroError,
    PaymentOfThisPurposeMustHaveAppointmentError,
    PaymentOfThisTypeDoesNotNeedAVipClient,
    VipClientHasInsufficientCreditError,
    VipClientIdIsRequiredError,
)
from app.core.exceptions.users import VipClientNotFoundError
from app.core.types.client_credit_source_type import ClientCreditSourceType
from app.core.types.payment_enums import PaymentMethodType, PaymentPurposeType
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo


def make_retry_input(*, payment, actor):
    return CreatePaymentInput(
        idempotency_key=payment.id,
        actor=actor,
        amount=payment.amount,
        payment_method=payment.payment_method,
        payment_purpose=payment.payment_purpose,
        appointment_id=payment.appointment_id,
        credit_owner_vip_client_id=payment.vip_client_id,
        description=payment.description,
        external_reference=payment.external_reference,
    )


async def test_first_request_uses_idempotency_key_as_payment_id(
    write_uow,
    make_user,
    make_vip_client,
    make_quoted_appointment,
    make_client_credit_entry,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)
    appointment = make_quoted_appointment(user_id=actor.id)
    write_uow.appointments.create(appointment)
    write_uow.client_credit_entries.create(
        make_client_credit_entry(vip_client_id=vip_client.id, quantity=100)
    )
    idempotency_key = uuid4()
    data = CreatePaymentInput(
        idempotency_key=idempotency_key,
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.CLIENT_CREDIT,
        payment_purpose=PaymentPurposeType.APPOINTMENT,
        appointment_id=appointment.id,
        credit_owner_vip_client_id=vip_client.id,
        description="pagamento com créditos",
        external_reference=None,
    )

    result = await CreatePaymentUseCase(
        write_uow, fake_transactional_event_bus, fake_integration_event_bus
    ).execute(data)

    assert result.payment_id == idempotency_key
    assert write_uow.payments.find_by_id(idempotency_key) is not None


async def test_retry_returns_existing_payment_without_creating_side_effects(
    write_uow,
    make_user,
    make_payment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    payment_id = uuid4()
    payment = make_payment(id=payment_id)
    write_uow.payments.create(payment)
    data = make_retry_input(payment=payment, actor=actor)

    result = await CreatePaymentUseCase(
        write_uow, fake_transactional_event_bus, fake_integration_event_bus
    ).execute(data)

    assert payment.id == payment_id
    assert result.payment_id == payment_id
    assert result.amount == payment.amount
    assert write_uow.payments.count_by_vip_client_id(payment.vip_client_id) == 1
    assert write_uow.client_credit_entries.count_by_source_id(source_id=payment.id) == 0
    assert write_uow.audit_logs.find_many_by_entity_name(entity_name="payments") == []
    assert fake_transactional_event_bus.events == []


@pytest.mark.parametrize(
    ("field", "different_value"),
    [
        ("amount", Decimal("11")),
        ("payment_method", PaymentMethodType.CARD),
        ("payment_purpose", PaymentPurposeType.DEPOSIT),
        ("appointment_id", uuid4()),
        ("credit_owner_vip_client_id", uuid4()),
        ("description", "outro pagamento"),
        ("external_reference", "outra-referencia"),
    ],
)
async def test_reusing_key_with_different_payment_data_raises_conflict(
    field,
    different_value,
    write_uow,
    make_user,
    make_payment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    payment = make_payment()
    write_uow.payments.create(payment)
    data = replace(
        make_retry_input(payment=payment, actor=actor),
        **{field: different_value},
    )

    with pytest.raises(IdempotencyKeyConflictError):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)


async def test_duplicate_external_reference_raises_conflict(
    write_uow,
    make_user,
    make_payment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    existing_payment = make_payment(external_reference="provider-reference")
    write_uow.payments.create(existing_payment)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.OTHER,
        description="manual payment",
        external_reference="provider-reference",
    )

    with pytest.raises(DuplicateExternalReferenceError):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)

    assert write_uow.payments.find_by_id(data.idempotency_key) is None


async def test_external_reference_is_persisted_and_included_in_audit_log(
    write_uow,
    make_user,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.OTHER,
        description="manual payment",
        external_reference="provider-reference",
    )

    await CreatePaymentUseCase(
        write_uow, fake_transactional_event_bus, fake_integration_event_bus
    ).execute(data)

    payment = write_uow.payments.find_by_id(data.idempotency_key)
    logs = write_uow.audit_logs.find_many_by_entity_id(data.idempotency_key)
    assert payment is not None
    assert payment.external_reference == "provider-reference"
    assert logs[0].changes["creation_state_must_important_info"]["external_reference"] == (
        "provider-reference"
    )


@pytest.mark.parametrize(
    "purpose",
    [PaymentPurposeType.APPOINTMENT, PaymentPurposeType.DEPOSIT],
)
async def test_payable_purpose_requires_appointment(
    purpose,
    write_uow,
    make_user,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=purpose,
        appointment_id=None,
        description="pagamento",
    )

    with pytest.raises(PaymentOfThisPurposeMustHaveAppointmentError):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)


async def test_payable_purpose_rejects_unknown_appointment(
    write_uow,
    make_user,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.APPOINTMENT,
        appointment_id=uuid4(),
        description="pagamento",
    )

    with pytest.raises(AppointmentNotFoundError):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)


@pytest.mark.parametrize("purpose", [PaymentPurposeType.TIP, PaymentPurposeType.OTHER])
async def test_optional_appointment_must_exist_when_provided(
    purpose,
    write_uow,
    make_user,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=make_user(),
        amount=Decimal("10"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=purpose,
        appointment_id=uuid4(),
        description="linked payment",
    )

    with pytest.raises(AppointmentNotFoundError):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)


@pytest.mark.parametrize("purpose", [PaymentPurposeType.TIP, PaymentPurposeType.OTHER])
async def test_optional_appointment_can_be_linked_when_it_exists(
    purpose,
    write_uow,
    make_user,
    make_appointment_base,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    appointment = make_appointment_base(user_id=actor.id)
    write_uow.appointments.create(appointment)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=purpose,
        appointment_id=appointment.id,
        description="linked payment",
    )

    result = await CreatePaymentUseCase(
        write_uow, fake_transactional_event_bus, fake_integration_event_bus
    ).execute(data)

    assert result.appointment_id == appointment.id


@pytest.fixture
def make_client_credit_payment_input():
    def factory(*, actor, vip_client_id, appointment_id, amount):
        return CreatePaymentInput(
            idempotency_key=uuid4(),
            actor=actor,
            amount=amount,
            payment_method=PaymentMethodType.CLIENT_CREDIT,
            payment_purpose=PaymentPurposeType.APPOINTMENT,
            appointment_id=appointment_id,
            credit_owner_vip_client_id=vip_client_id,
            description="pagamento com créditos",
            external_reference=None,
        )

    return factory


@pytest.fixture
def arrange_client_credit_payment(
    write_uow,
    make_user,
    make_vip_client,
    make_quoted_appointment,
    make_client_credit_entry,
    make_client_credit_payment_input,
):
    def factory(*, balance, amount):
        actor = make_user()
        write_uow.users.create(actor)
        vip_client = make_vip_client()
        write_uow.vip_clients.create(vip_client)
        appointment = make_quoted_appointment(user_id=actor.id)
        write_uow.appointments.create(appointment)
        write_uow.client_credit_entries.create(
            make_client_credit_entry(vip_client_id=vip_client.id, quantity=balance)
        )
        data = make_client_credit_payment_input(
            actor=actor,
            vip_client_id=vip_client.id,
            appointment_id=appointment.id,
            amount=amount,
        )
        return actor, vip_client, appointment, data

    return factory


@pytest.mark.parametrize(
    ("amount", "expected_debit"),
    [
        (Decimal("10.00"), -10),
        (Decimal("10.99"), -10),
    ],
)
async def test_client_credit_payment_creates_payment_and_expected_debit(
    amount,
    expected_debit,
    write_uow,
    arrange_client_credit_payment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    _, vip_client, appointment, data = arrange_client_credit_payment(
        balance=10,
        amount=amount,
    )

    result = await CreatePaymentUseCase(
        write_uow, fake_transactional_event_bus, fake_integration_event_bus
    ).execute(data)

    payment = write_uow.payments.find_by_id(result.payment_id)
    assert payment is not None
    assert payment.amount == amount
    assert payment.vip_client_id == vip_client.id
    assert payment.appointment_id == appointment.id

    entries = write_uow.client_credit_entries.find_many_by_source_id(source_id=payment.id)
    assert len(entries) == 1
    debit = entries[0]
    assert debit.vip_client_id == vip_client.id
    assert debit.source_type == ClientCreditSourceType.USED_AS_PAYMENT
    assert debit.quantity == expected_debit
    assert write_uow.client_credit_entries.get_balance(vip_client_id=vip_client.id) == 0


async def test_client_credit_payment_with_insufficient_balance_has_no_side_effects(
    write_uow,
    arrange_client_credit_payment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    _, vip_client, _, data = arrange_client_credit_payment(
        balance=9,
        amount=Decimal("10.99"),
    )

    with pytest.raises(VipClientHasInsufficientCreditError):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)

    assert write_uow.payments.find_by_id(data.idempotency_key) is None
    assert write_uow.client_credit_entries.get_balance(vip_client_id=vip_client.id) == 9
    assert write_uow.audit_logs.find_many_by_entity_name(entity_name="payments") == []


async def test_client_credit_payment_below_one_real_raises_specific_error(
    write_uow,
    arrange_client_credit_payment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    _, vip_client, _, data = arrange_client_credit_payment(
        balance=10,
        amount=Decimal("0.99"),
    )

    with pytest.raises(PaymentConsumesZeroClientCreditsError):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)

    assert write_uow.payments.find_by_id(data.idempotency_key) is None
    assert write_uow.client_credit_entries.get_balance(vip_client_id=vip_client.id) == 10


async def test_non_credit_payment_does_not_create_credit_entry(
    write_uow,
    make_user,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("0.50"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.OTHER,
        appointment_id=None,
        credit_owner_vip_client_id=None,
        description="pagamento avulso",
        external_reference=None,
    )

    result = await CreatePaymentUseCase(
        write_uow, fake_transactional_event_bus, fake_integration_event_bus
    ).execute(data)

    payment = write_uow.payments.find_by_id(result.payment_id)
    assert payment is not None
    assert payment.amount == Decimal("0.50")
    assert payment.vip_client_id is None
    assert write_uow.client_credit_entries.count_by_source_id(source_id=payment.id) == 0


async def test_client_credit_payment_requires_vip_client_id(
    write_uow,
    make_user,
    make_quoted_appointment,
    make_client_credit_payment_input,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    appointment = make_quoted_appointment(user_id=actor.id)
    write_uow.appointments.create(appointment)
    data = make_client_credit_payment_input(
        actor=actor,
        vip_client_id=None,
        appointment_id=appointment.id,
        amount=Decimal("10"),
    )

    with pytest.raises(VipClientIdIsRequiredError):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)

    assert write_uow.payments.find_by_id(data.idempotency_key) is None


async def test_client_credit_payment_rejects_unknown_vip_client(
    write_uow,
    make_user,
    make_quoted_appointment,
    make_client_credit_payment_input,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    appointment = make_quoted_appointment(user_id=actor.id)
    write_uow.appointments.create(appointment)
    data = make_client_credit_payment_input(
        actor=actor,
        vip_client_id=uuid4(),
        appointment_id=appointment.id,
        amount=Decimal("10"),
    )

    with pytest.raises(VipClientNotFoundError):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)

    assert write_uow.payments.find_by_id(data.idempotency_key) is None


async def test_client_credit_payment_creates_payment_and_credit_audit_logs(
    write_uow,
    arrange_client_credit_payment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor, vip_client, _, data = arrange_client_credit_payment(
        balance=10,
        amount=Decimal("10"),
    )

    result = await CreatePaymentUseCase(
        write_uow, fake_transactional_event_bus, fake_integration_event_bus
    ).execute(data)

    payment_logs = write_uow.audit_logs.find_many_by_entity_name(entity_name="payments")
    credit_logs = write_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry")
    assert len(payment_logs) == 1
    assert payment_logs[0].entity_id == result.payment_id
    assert payment_logs[0].actor_id == actor.id
    assert len(credit_logs) == 1
    assert credit_logs[0].actor_id == actor.id
    assert credit_logs[0].changes["vip_client_id"] == str(vip_client.id)
    assert credit_logs[0].changes["credits_deducted"] == "10"


async def test_non_credit_payment_creates_only_payment_audit_log(
    write_uow,
    make_user,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.CASH,
        payment_purpose=PaymentPurposeType.OTHER,
        description="pagamento avulso",
    )

    await CreatePaymentUseCase(
        write_uow, fake_transactional_event_bus, fake_integration_event_bus
    ).execute(data)

    assert len(write_uow.audit_logs.find_many_by_entity_name(entity_name="payments")) == 1
    assert write_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry") == []


async def test_non_credit_payment_rejects_credit_owner(
    write_uow,
    make_user,
    make_vip_client,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.OTHER,
        credit_owner_vip_client_id=vip_client.id,
        description="pagamento avulso",
    )

    with pytest.raises(PaymentOfThisTypeDoesNotNeedAVipClient):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)


async def test_client_credit_payment_locks_credit_owner(
    monkeypatch,
    write_uow,
    arrange_client_credit_payment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    _, vip_client, _, data = arrange_client_credit_payment(
        balance=10,
        amount=Decimal("10"),
    )
    locked_ids = []
    original_find = write_uow.vip_clients.find_by_id_for_update

    def find_by_id_for_update(vip_client_id):
        locked_ids.append(vip_client_id)
        return original_find(vip_client_id)

    monkeypatch.setattr(write_uow.vip_clients, "find_by_id_for_update", find_by_id_for_update)

    await CreatePaymentUseCase(
        write_uow, fake_transactional_event_bus, fake_integration_event_bus
    ).execute(data)

    assert locked_ids == [vip_client.id]


async def test_client_credit_payment_validates_payment_amount_before_conversion(
    write_uow,
    make_user,
    make_vip_client,
    make_quoted_appointment,
    make_client_credit_payment_input,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)
    appointment = make_quoted_appointment(user_id=actor.id)
    write_uow.appointments.create(appointment)
    data = make_client_credit_payment_input(
        actor=actor,
        vip_client_id=vip_client.id,
        appointment_id=appointment.id,
        amount=Decimal("-0.50"),
    )

    with pytest.raises(PaymentMustBeGreaterThanZeroError):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)


async def test_client_credit_can_pay_other_purpose_without_appointment(
    write_uow,
    make_user,
    make_vip_client,
    make_client_credit_entry,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)
    write_uow.client_credit_entries.create(
        make_client_credit_entry(vip_client_id=vip_client.id, quantity=10)
    )
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.CLIENT_CREDIT,
        payment_purpose=PaymentPurposeType.OTHER,
        appointment_id=None,
        credit_owner_vip_client_id=vip_client.id,
        description="produto avulso",
    )

    result = await CreatePaymentUseCase(
        write_uow, fake_transactional_event_bus, fake_integration_event_bus
    ).execute(data)

    assert result.appointment_id is None
    assert write_uow.client_credit_entries.get_balance(vip_client_id=vip_client.id) == 0


async def test_deposit_payment_publishes_event(
    write_uow,
    make_user,
    make_quoted_appointment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    appointment = make_quoted_appointment(user_id=actor.id)
    write_uow.appointments.create(appointment)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.DEPOSIT,
        appointment_id=appointment.id,
        description="caução",
    )

    await CreatePaymentUseCase(
        write_uow, fake_transactional_event_bus, fake_integration_event_bus
    ).execute(data)

    assert len(fake_transactional_event_bus.events) == 1
    event = fake_transactional_event_bus.events[0]
    assert event.appointment_id == appointment.id
    assert event.amount == Decimal("10")

    assert len(fake_integration_event_bus.events) == 1
    email_event = fake_integration_event_bus.events[0]
    assert email_event.client_email == appointment.client_info.email
    assert email_event.amount == Decimal("10")
    assert email_event.appointment_type == appointment.appointment_type
    assert email_event.start_at == appointment.start_at


async def test_deposit_confirmation_uses_vip_client_email(
    write_uow,
    make_user,
    make_vip_client,
    make_quoted_appointment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    vip_client = make_vip_client(email="vip@email.com")
    write_uow.vip_clients.create(vip_client)
    appointment = make_quoted_appointment(
        user_id=actor.id,
        client_info=ClientInfo(vip_client_id=vip_client.id),
    )
    write_uow.appointments.create(appointment)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("50"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.DEPOSIT,
        appointment_id=appointment.id,
    )

    await CreatePaymentUseCase(
        write_uow, fake_transactional_event_bus, fake_integration_event_bus
    ).execute(data)

    assert len(fake_integration_event_bus.events) == 1
    assert fake_integration_event_bus.events[0].client_email == "vip@email.com"


async def test_deposit_confirmation_rejects_missing_vip_client_reference(
    write_uow,
    make_user,
    make_quoted_appointment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    appointment = make_quoted_appointment(
        user_id=actor.id,
        client_info=ClientInfo(vip_client_id=uuid4()),
    )
    write_uow.appointments.create(appointment)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("50"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.DEPOSIT,
        appointment_id=appointment.id,
    )

    with pytest.raises(AppointmentClientInfoBreakingDomainRules):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)

    assert fake_integration_event_bus.events == []


async def test_deposit_payment_rejects_appointment_not_quoted(
    write_uow,
    make_user,
    make_scheduled_appointment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    appointment = make_scheduled_appointment(user_id=actor.id)
    write_uow.appointments.create(appointment)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.DEPOSIT,
        appointment_id=appointment.id,
        description="caução",
    )

    with pytest.raises(IncorrectAppointmentStatusError):
        await CreatePaymentUseCase(
            write_uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)

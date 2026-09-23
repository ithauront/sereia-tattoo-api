from decimal import Decimal
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.dependencies.auth import get_current_active_user, get_current_user
from app.api.dependencies.events import get_integration_event_bus, get_transactional_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.api.error_handlers import PAYMENT_ERROR_RESPONSES, domain_exception_handler
from app.application.event_bus.transactional_event_bus import TransactionalEventBus
from app.application.studio.handlers.confirm_deposit import ConfirmDepositHandler
from app.core.types.appointment_enums import AppointmentStatus
from app.core.types.client_credit_source_type import ClientCreditSourceType
from app.core.types.payment_enums import PaymentMethodType, PaymentPurposeType
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.finances.events.deposit_payment_recorded_event import (
    DepositPaymentRecordedEvent,
)
from app.main import app

EXPECTED_PAYMENT_ERROR_RESPONSES = {
    "AppointmentNotFoundError": (404, "appointment_not_found"),
    "VipClientNotFoundError": (404, "vip_client_not_found"),
    "DuplicateExternalReferenceError": (409, "external_reference_already_exists"),
    "IdempotencyKeyConflictError": (409, "idempotency_key_conflict"),
    "IncorrectAppointmentStatusError": (
        409,
        "appointment_cannot_accept_deposit_in_current_status",
    ),
    "AppointmentMustBeInCorrectPreviousStatusError": (
        409,
        "appointment_cannot_accept_deposit_in_current_status",
    ),
    "VipClientHasInsufficientCreditError": (409, "vip_client_has_insufficient_credit"),
    "PaymentOfThisTypeDoesNotNeedAVipClient": (
        422,
        "credit_owner_is_only_allowed_for_client_credit_payments",
    ),
    "PaymentOfThisPurposeMustHaveAppointmentError": (
        422,
        "appointment_id_is_required_for_this_payment_purpose",
    ),
    "VipClientIdIsRequiredError": (422, "credit_owner_vip_client_id_is_required"),
    "PaymentWithoutAppointmentRequireDescriptionError": (
        422,
        "description_is_required_when_appointment_id_is_not_provided",
    ),
    "PaymentConsumesZeroClientCreditsError": (
        422,
        "client_credit_payment_must_consume_at_least_one_credit",
    ),
    "PaymentMustBeGreaterThanZeroError": (422, "payment_amount_must_be_greater_than_zero"),
    "PaymentAmountExceedsMaximumError": (422, "payment_amount_exceeds_maximum"),
    "PaymentAmountHasSubCentPrecisionError": (
        422,
        "payment_amount_must_have_at_most_two_decimal_places",
    ),
    "InvalidPaymentAmountError": (422, "payment_amount_must_be_finite"),
    "AppointmentClientInfoBreakingDomainRules": (500, "appointment_data_is_inconsistent"),
    "PriceMustBeDefinedError": (500, "appointment_data_is_inconsistent"),
    "PaymentLinkToAppointmentIsCorruptedError": (500, "payment_data_is_inconsistent"),
    "PaymentMustHaveDepositPurposeError": (500, "payment_data_is_inconsistent"),
    "CreditMustBePositiveError": (500, "client_credit_data_is_inconsistent"),
    "ZeroCreditQuantityNotAllowedError": (500, "client_credit_data_is_inconsistent"),
}


@pytest.fixture
def payment_route_dependencies(
    write_uow,
    read_uow,
    fake_integration_event_bus,
    fake_transactional_event_bus,
):
    dependencies = {
        "actor": None,
        "transactional_bus": fake_transactional_event_bus,
    }

    async def current_user_override():
        return dependencies["actor"]

    async def write_uow_override():
        return write_uow

    async def read_uow_override():
        return read_uow

    async def integration_bus_override():
        return fake_integration_event_bus

    async def transactional_bus_override():
        return dependencies["transactional_bus"]

    app.dependency_overrides[get_current_active_user] = current_user_override
    app.dependency_overrides[get_write_unit_of_work] = write_uow_override
    app.dependency_overrides[get_read_unit_of_work] = read_uow_override
    app.dependency_overrides[get_integration_event_bus] = integration_bus_override
    app.dependency_overrides[get_transactional_event_bus] = transactional_bus_override

    def configure(*, actor, transactional_bus=None):
        dependencies["actor"] = actor
        if transactional_bus is not None:
            dependencies["transactional_bus"] = transactional_bus

    yield configure
    app.dependency_overrides = {}


def payment_payload(**overrides):
    payload = {
        "idempotency_key": str(uuid4()),
        "amount": "10.50",
        "payment_method": PaymentMethodType.PIX.value,
        "payment_purpose": PaymentPurposeType.OTHER.value,
        "description": "manual payment",
    }
    payload.update(overrides)
    return payload


async def post_payment(payload):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/payments", json=payload)


@pytest.mark.parametrize(
    "payment_method",
    [PaymentMethodType.CASH, PaymentMethodType.CARD, PaymentMethodType.PIX],
)
async def test_create_standalone_payment_with_common_methods(
    payment_method,
    payment_route_dependencies,
    write_uow,
    read_uow,
    make_user,
):
    actor = make_user()
    write_uow.users.create(actor)
    payment_route_dependencies(actor=actor)
    payment_id = uuid4()

    response = await post_payment(
        payment_payload(
            idempotency_key=str(payment_id),
            amount="10,50",
            payment_method=payment_method.value,
        ),
    )

    assert response.status_code == 201
    assert response.json() == {
        "payment_id": str(payment_id),
        "amount": "10.50",
        "payment_method": payment_method.value,
        "payment_purpose": PaymentPurposeType.OTHER.value,
        "appointment_id": None,
        "vip_client_id": None,
        "created_at": response.json()["created_at"],
    }
    persisted = read_uow.payments.find_by_id(payment_id)
    assert persisted is not None
    assert persisted.amount == Decimal("10.50")
    assert len(read_uow.audit_logs.find_many_by_entity_id(payment_id)) == 1


@pytest.mark.parametrize(
    "purpose",
    [PaymentPurposeType.APPOINTMENT, PaymentPurposeType.TIP, PaymentPurposeType.OTHER],
)
async def test_create_payment_linked_to_appointment(
    purpose,
    payment_route_dependencies,
    write_uow,
    read_uow,
    make_user,
    make_quoted_appointment,
):
    actor = make_user()
    write_uow.users.create(actor)
    payment_route_dependencies(actor=actor)
    appointment = make_quoted_appointment(user_id=actor.id)
    write_uow.appointments.create(appointment)

    response = await post_payment(
        payment_payload(
            payment_purpose=purpose.value,
            appointment_id=str(appointment.id),
        ),
    )

    assert response.status_code == 201
    assert response.json()["appointment_id"] == str(appointment.id)
    assert len(read_uow.payments.find_many_by_appointment_id(appointment.id)) == 1


async def test_create_client_credit_payment_deducts_credits(
    payment_route_dependencies,
    write_uow,
    read_uow,
    make_user,
    make_vip_client,
    make_quoted_appointment,
    make_client_credit_entry,
):
    actor = make_user()
    write_uow.users.create(actor)
    payment_route_dependencies(actor=actor)
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)
    appointment = make_quoted_appointment(user_id=actor.id)
    write_uow.appointments.create(appointment)
    write_uow.client_credit_entries.create(
        make_client_credit_entry(vip_client_id=vip_client.id, quantity=20)
    )

    response = await post_payment(
        payment_payload(
            amount="10.99",
            payment_method=PaymentMethodType.CLIENT_CREDIT.value,
            payment_purpose=PaymentPurposeType.APPOINTMENT.value,
            appointment_id=str(appointment.id),
            credit_owner_vip_client_id=str(vip_client.id),
        ),
    )

    assert response.status_code == 201
    assert response.json()["vip_client_id"] == str(vip_client.id)
    assert read_uow.client_credit_entries.get_balance(vip_client_id=vip_client.id) == 10
    debit = read_uow.client_credit_entries.find_many_by_source_id(
        source_id=UUID(response.json()["payment_id"])
    )
    assert len(debit) == 1
    assert debit[0].source_type == ClientCreditSourceType.USED_AS_PAYMENT
    assert debit[0].quantity == -10


async def test_create_deposit_payment_confirms_appointment(
    payment_route_dependencies,
    write_uow,
    make_user,
    make_quoted_appointment,
    fake_integration_event_bus,
):
    actor = make_user()
    write_uow.users.create(actor)
    appointment = make_quoted_appointment(user_id=actor.id)
    write_uow.appointments.create(appointment)
    transactional_bus = TransactionalEventBus()
    transactional_bus.register(DepositPaymentRecordedEvent, ConfirmDepositHandler())
    payment_route_dependencies(actor=actor, transactional_bus=transactional_bus)

    response = await post_payment(
        payment_payload(
            amount="50",
            payment_purpose=PaymentPurposeType.DEPOSIT.value,
            appointment_id=str(appointment.id),
        ),
    )

    assert response.status_code == 201
    assert appointment.status == AppointmentStatus.SCHEDULED
    assert appointment.deposit_confirmed_at is not None
    assert len(fake_integration_event_bus.events) == 1


async def test_retry_with_same_idempotency_key_returns_existing_payment(
    payment_route_dependencies,
    write_uow,
    read_uow,
    make_user,
):
    actor = make_user()
    write_uow.users.create(actor)
    payment_route_dependencies(actor=actor)
    payload = payment_payload()

    first_response = await post_payment(payload)
    second_response = await post_payment(payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert second_response.json() == first_response.json()
    assert read_uow.payments.find_by_id(UUID(first_response.json()["payment_id"])) is not None
    assert len(read_uow.audit_logs.find_many_by_entity_name(entity_name="payments")) == 1


async def test_idempotency_conflict_is_returned_by_real_use_case(
    payment_route_dependencies,
    write_uow,
    make_user,
):
    actor = make_user()
    write_uow.users.create(actor)
    payment_route_dependencies(actor=actor)
    payload = payment_payload()
    first_response = await post_payment(payload)

    response = await post_payment({**payload, "amount": "11.00"})

    assert first_response.status_code == 201
    assert response.status_code == 409
    assert response.json()["detail"] == "idempotency_key_conflict"


async def test_duplicate_external_reference_is_returned_by_real_use_case(
    payment_route_dependencies,
    write_uow,
    make_user,
):
    actor = make_user()
    write_uow.users.create(actor)
    payment_route_dependencies(actor=actor)
    first_response = await post_payment(payment_payload(external_reference="provider-reference"))

    response = await post_payment(payment_payload(external_reference="provider-reference"))

    assert first_response.status_code == 201
    assert response.status_code == 409
    assert response.json()["detail"] == "external_reference_already_exists"


@pytest.mark.parametrize("purpose", [PaymentPurposeType.DEPOSIT, PaymentPurposeType.APPOINTMENT])
async def test_payable_payment_requires_appointment_through_http(
    purpose,
    payment_route_dependencies,
    write_uow,
    make_user,
):
    actor = make_user()
    write_uow.users.create(actor)
    payment_route_dependencies(actor=actor)

    response = await post_payment(payment_payload(payment_purpose=purpose.value))

    assert response.status_code == 422
    assert response.json()["detail"] == "appointment_id_is_required_for_this_payment_purpose"


async def test_unknown_appointment_is_returned_by_real_use_case(
    payment_route_dependencies,
    write_uow,
    make_user,
):
    actor = make_user()
    write_uow.users.create(actor)
    payment_route_dependencies(actor=actor)

    response = await post_payment(
        payment_payload(
            payment_purpose=PaymentPurposeType.OTHER.value,
            appointment_id=str(uuid4()),
        )
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "appointment_not_found"


async def test_client_credit_errors_are_returned_by_real_use_case(
    payment_route_dependencies,
    write_uow,
    make_user,
    make_vip_client,
    make_quoted_appointment,
    make_client_credit_entry,
):
    actor = make_user()
    write_uow.users.create(actor)
    appointment = make_quoted_appointment(user_id=actor.id)
    write_uow.appointments.create(appointment)
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)
    write_uow.client_credit_entries.create(
        make_client_credit_entry(vip_client_id=vip_client.id, quantity=5)
    )
    payment_route_dependencies(actor=actor)
    base_payload = payment_payload(
        payment_method=PaymentMethodType.CLIENT_CREDIT.value,
        payment_purpose=PaymentPurposeType.APPOINTMENT.value,
        appointment_id=str(appointment.id),
    )

    missing_owner = await post_payment(base_payload)
    unknown_owner = await post_payment(
        {**base_payload, "idempotency_key": str(uuid4()), "credit_owner_vip_client_id": str(uuid4())}
    )
    insufficient_balance = await post_payment(
        {
            **base_payload,
            "idempotency_key": str(uuid4()),
            "credit_owner_vip_client_id": str(vip_client.id),
        }
    )
    consumes_zero = await post_payment(
        {
            **base_payload,
            "idempotency_key": str(uuid4()),
            "amount": "0.99",
            "credit_owner_vip_client_id": str(vip_client.id),
        }
    )

    assert (missing_owner.status_code, missing_owner.json()["detail"]) == (
        422,
        "credit_owner_vip_client_id_is_required",
    )
    assert (unknown_owner.status_code, unknown_owner.json()["detail"]) == (
        404,
        "vip_client_not_found",
    )
    assert (insufficient_balance.status_code, insufficient_balance.json()["detail"]) == (
        409,
        "vip_client_has_insufficient_credit",
    )
    assert (consumes_zero.status_code, consumes_zero.json()["detail"]) == (
        422,
        "client_credit_payment_must_consume_at_least_one_credit",
    )


async def test_deposit_in_wrong_status_is_returned_by_real_use_case(
    payment_route_dependencies,
    write_uow,
    make_user,
    make_scheduled_appointment,
):
    actor = make_user()
    write_uow.users.create(actor)
    appointment = make_scheduled_appointment(user_id=actor.id)
    write_uow.appointments.create(appointment)
    payment_route_dependencies(actor=actor)

    response = await post_payment(
        payment_payload(
            payment_purpose=PaymentPurposeType.DEPOSIT.value,
            appointment_id=str(appointment.id),
        )
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "appointment_cannot_accept_deposit_in_current_status"


async def test_inconsistent_appointment_client_is_returned_by_real_use_case(
    payment_route_dependencies,
    write_uow,
    make_user,
    make_quoted_appointment,
):
    actor = make_user()
    write_uow.users.create(actor)
    appointment = make_quoted_appointment(
        user_id=actor.id,
        client_info=ClientInfo(vip_client_id=uuid4()),
    )
    write_uow.appointments.create(appointment)
    payment_route_dependencies(actor=actor)

    response = await post_payment(
        payment_payload(
            payment_purpose=PaymentPurposeType.DEPOSIT.value,
            appointment_id=str(appointment.id),
        )
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "appointment_data_is_inconsistent"


async def test_standalone_payment_requires_description_through_http(
    payment_route_dependencies,
    write_uow,
    make_user,
):
    actor = make_user()
    write_uow.users.create(actor)
    payment_route_dependencies(actor=actor)

    response = await post_payment(payment_payload(description="   "))

    assert response.status_code == 422
    assert response.json()["detail"] == "description_is_required_when_appointment_id_is_not_provided"


async def test_non_credit_payment_rejects_credit_owner_through_http(
    payment_route_dependencies,
    write_uow,
    make_user,
):
    actor = make_user()
    write_uow.users.create(actor)
    payment_route_dependencies(actor=actor)

    response = await post_payment(payment_payload(credit_owner_vip_client_id=str(uuid4())))

    assert response.status_code == 422
    assert response.json()["detail"] == ("credit_owner_is_only_allowed_for_client_credit_payments")


@pytest.mark.parametrize(
    "overrides",
    [
        {"amount": "0"},
        {"amount": "-0.01"},
        {"amount": "10.001"},
        {"amount": "100000000.00"},
        {"amount": "not-a-number"},
        {"idempotency_key": "not-a-uuid"},
        {"payment_method": "bank_transfer"},
        {"payment_purpose": "subscription"},
        {"external_reference": "x" * 256},
    ],
)
async def test_invalid_payment_schema_returns_unprocessable_content(
    overrides,
    payment_route_dependencies,
    make_user,
):
    payment_route_dependencies(actor=make_user())

    response = await post_payment(payment_payload(**overrides))

    assert response.status_code == 422


@pytest.mark.parametrize(
    "missing_field",
    ["idempotency_key", "amount", "payment_method", "payment_purpose"],
)
async def test_missing_required_payment_field_returns_unprocessable_content(
    missing_field,
    payment_route_dependencies,
    make_user,
):
    payment_route_dependencies(actor=make_user())
    payload = payment_payload()
    payload.pop(missing_field)

    response = await post_payment(payload)

    assert response.status_code == 422


def test_current_active_user_dependency_rejects_inactive_user(make_user):
    actor = make_user(is_active=False)

    with pytest.raises(HTTPException) as raised:
        get_current_active_user(user=actor)

    assert raised.value.status_code == 403
    assert raised.value.detail == "inactive_user"


def test_current_user_dependency_rejects_token_for_unknown_user(
    read_uow,
    make_user,
    make_token,
    access_token_service,
):
    unknown_user = make_user()

    with pytest.raises(HTTPException) as raised:
        get_current_user(
            authorization=f"Bearer {make_token(unknown_user)}",
            uow=read_uow,
            access_tokens=access_token_service,
        )

    assert raised.value.status_code == 401
    assert raised.value.detail == "invalid_credentials"


@pytest.mark.parametrize(
    ("domain_error", "expected_status", "expected_detail"),
    [
        (error_type(), *EXPECTED_PAYMENT_ERROR_RESPONSES[error_type.__name__])
        for error_type in PAYMENT_ERROR_RESPONSES
    ],
)
async def test_create_payment_translates_domain_errors_to_http(
    domain_error,
    expected_status,
    expected_detail,
):
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/payments",
            "headers": [],
            "route": type("Route", (), {"name": "create_payment"})(),
        }
    )

    response = await domain_exception_handler(request, domain_error)

    assert response.status_code == expected_status
    assert response.body == httpx.Response(200, json={"detail": expected_detail}).content


def test_payments_router_is_registered():
    assert any(route.path == "/payments" and "POST" in route.methods for route in app.routes)


def test_payment_error_mapping_matches_explicit_contract():
    assert {error.__name__ for error in PAYMENT_ERROR_RESPONSES} == set(EXPECTED_PAYMENT_ERROR_RESPONSES)


def test_route_uses_current_active_user_dependency():
    payment_route = next(route for route in app.routes if route.path == "/payments")

    assert any(
        dependency.call is get_current_active_user for dependency in payment_route.dependant.dependencies
    )

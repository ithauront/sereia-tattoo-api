from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application.studio.use_cases.DTO.commun import Direction
from app.core.exceptions.payment import DuplicateExternalReferenceError
from app.domain.studio.finances.entities.payment import Payment
from app.core.types.payment_enums import PaymentMethodType
from tests.fakes.fake_appointments_repository import FakeAppointmentsRepository
from tests.fakes.fake_payments_repository import FakePaymentsRepository
from tests.fakes.fake_vip_clients_repository import FakeVipClientsRepository


@pytest.fixture
def payments_repo():
    return FakePaymentsRepository()


@pytest.fixture
def appointments_repo():
    return FakeAppointmentsRepository()


@pytest.fixture
def vip_client_repo():
    return FakeVipClientsRepository()


def test_create_and_find_by_id(make_payment, payments_repo):
    payment = make_payment(amount=Decimal("10"))
    payments_repo.create(payment)

    found = payments_repo.find_by_id(payment.id)

    assert found is not None

    assert found.id == payment.id
    assert found.amount == Decimal("10")
    assert found.payment_method == PaymentMethodType.PIX
    assert found.description == "Pagamento da tatuagem"
    assert found.vip_client_id == payment.vip_client_id
    assert found.appointment_id == payment.appointment_id
    assert found.external_reference == payment.external_reference


def test_do_not_found_by_id(make_payment, payments_repo):
    payment = make_payment(amount=Decimal("10"))
    # we do not persist for this test

    found = payments_repo.find_by_id(payment.id)

    assert found is None


def test_find_many_by_vip_client_id_dsc(
    make_payment, payments_repo, vip_client_repo, make_vip_client
):
    vip_client = make_vip_client()
    vip_client_repo.create(vip_client)

    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        created_at = base_now + timedelta(seconds=i)
        amount = i + 1
        payment = make_payment(
            vip_client_id=vip_client.id,
            amount=Decimal(str(amount)),
            created_at=created_at,
        )
        payments_repo.create(payment)

    founds = payments_repo.find_many_by_vip_client_id(
        vip_client_id=vip_client.id, limit=5, offset=0
    )

    amounts = [p.amount for p in founds]
    # order is created last came first
    assert amounts == [
        Decimal("5"),
        Decimal("4"),
        Decimal("3"),
        Decimal("2"),
        Decimal("1"),
    ]


def test_find_many_by_vip_client_id_asc(
    make_payment, payments_repo, vip_client_repo, make_vip_client
):
    vip_client = make_vip_client()
    vip_client_repo.create(vip_client)
    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        amount = i + 1
        created_at = base_now + timedelta(seconds=i)
        payment = make_payment(
            vip_client_id=vip_client.id,
            amount=Decimal(str(amount)),
            created_at=created_at,
        )
        payments_repo.create(payment)

    founds = payments_repo.find_many_by_vip_client_id(
        vip_client_id=vip_client.id, limit=5, offset=0, direction=Direction.asc
    )

    amounts = [p.amount for p in founds]
    # order is created first came last
    assert amounts == [
        Decimal("1"),
        Decimal("2"),
        Decimal("3"),
        Decimal("4"),
        Decimal("5"),
    ]


def test_find_many_by_vip_client_id_offset_and_limit(
    make_payment, payments_repo, vip_client_repo, make_vip_client
):
    vip_client = make_vip_client()
    vip_client_repo.create(vip_client)
    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        amount = i + 1
        created_at = base_now + timedelta(seconds=i)
        payment = make_payment(
            vip_client_id=vip_client.id,
            amount=Decimal(str(amount)),
            created_at=created_at,
        )
        payments_repo.create(payment)

    founds = payments_repo.find_many_by_vip_client_id(
        vip_client_id=vip_client.id, limit=2, offset=1, direction=Direction.asc
    )

    amounts = [p.amount for p in founds]
    # offset 1 cut first result and limit 2 only return 2 entries
    # direction asc makes old entries come first
    assert amounts == [
        Decimal("2"),
        Decimal("3"),
    ]


def test_find_many_by_vip_client_not_found(
    make_payment,
    payments_repo,
):
    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    for i in range(5):
        amount = i + 1
        created_at = base_now + timedelta(seconds=i)
        payment = make_payment(amount=Decimal(str(amount)), created_at=created_at)
        payments_repo.create(payment)

    founds = payments_repo.find_many_by_vip_client_id(
        vip_client_id=uuid4(), limit=2, offset=1, direction=Direction.desc
    )

    assert founds == []


def test_count_by_vip_client_id(
    make_payment, payments_repo, vip_client_repo, make_vip_client
):
    vip_client = make_vip_client()
    vip_client_repo.create(vip_client)
    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    for i in range(5):
        created_at = base_now + timedelta(seconds=i)
        payment = make_payment(vip_client_id=vip_client.id, created_at=created_at)
        payments_repo.create(payment)

    total = payments_repo.count_by_vip_client_id(vip_client_id=vip_client.id)

    assert total == 5


def test_find_many_by_appointment_id(
    make_payment, payments_repo, appointments_repo, make_completed_appointment
):
    appointment = make_completed_appointment()
    appointments_repo.create(appointment)

    payment_deposit = make_payment(amount=Decimal("30"), appointment_id=appointment.id)
    payments_repo.create(payment_deposit)

    payment_tattoo = make_payment(amount=Decimal("670"), appointment_id=appointment.id)
    payments_repo.create(payment_tattoo)

    founds = payments_repo.find_many_by_appointment_id(appointment_id=appointment.id)

    assert len(founds) == 2

    amounts = [p.amount for p in founds]
    assert Decimal("30") in amounts
    assert Decimal("670") in amounts


def test_sum_by_vip_client_id(
    make_payment, payments_repo, vip_client_repo, make_vip_client
):
    vip_client = make_vip_client()
    vip_client_repo.create(vip_client)
    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    for i in range(5):
        amount = i + 1
        created_at = base_now + timedelta(seconds=i)
        payment = make_payment(
            vip_client_id=vip_client.id,
            amount=Decimal(str(amount)),
            created_at=created_at,
        )
        payments_repo.create(payment)

    total = payments_repo.sum_by_vip_client_id(vip_client_id=vip_client.id)

    assert total == Decimal("15")


def test_count_by_vip_client_id_zero(payments_repo):

    total = payments_repo.count_by_vip_client_id(uuid4())

    assert total == 0


def test_sum_by_appointment_id(
    make_payment, payments_repo, appointments_repo, make_completed_appointment
):
    appointment = make_completed_appointment()
    appointments_repo.create(appointment)
    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        amount = i + 1
        created_at = base_now + timedelta(seconds=i)
        payment = make_payment(
            appointment_id=appointment.id,
            amount=Decimal(str(amount)),
            created_at=created_at,
        )
        payments_repo.create(payment)

    total = payments_repo.sum_by_appointment_id(appointment_id=appointment.id)

    assert total == Decimal("15")


def test_find_by_external_reference(make_payment, payments_repo):
    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    for i in range(5):
        created_at = base_now + timedelta(seconds=i)
        payment = make_payment(
            external_reference=f"reference{i}", created_at=created_at
        )
        payments_repo.create(payment)

    reference_match = payments_repo.find_by_external_reference("reference0")

    assert reference_match is not None
    assert isinstance(reference_match, Payment)


def test_exists_by_external_reference_true(make_payment, payments_repo):
    payment = make_payment(external_reference="reference1")
    payments_repo.create(payment)

    exists = payments_repo.exists_by_external_reference("reference1")

    assert exists is True


def test_cannot_have_duplicate_external_reference(make_payment, payments_repo):
    payment1 = make_payment(external_reference="reference1")
    payments_repo.create(payment1)

    payment2 = make_payment(external_reference="reference1")

    with pytest.raises(DuplicateExternalReferenceError):
        payments_repo.create(payment2)


def test_exists_by_external_reference_false(make_payment, payments_repo):
    payment = make_payment(external_reference="reference1")
    payments_repo.create(payment)

    exists = payments_repo.exists_by_external_reference("reference0")

    assert exists is False


def test_can_have_multiple_null_external_reference(make_payment, payments_repo):
    payment1 = make_payment(external_reference=None)
    payment2 = make_payment(external_reference=None)

    payments_repo.create(payment1)
    payments_repo.create(payment2)

    assert True

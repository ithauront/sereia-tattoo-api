from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from app.application.event_bus.setup import setup_event_bus
from app.core.security import jwt_service
from app.core.security.jwt_service import JWTService
from app.core.security.passwords import hash_password
from app.core.security.versioned_token_service import VersionedTokenService
from app.domain.studio.appointments.entities.appointment import Appointment
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.appointments.enums.appointment_enums import (
    AppointmentStatus,
    AppointmentType,
)
from app.domain.studio.finances.entities.client_credit_entry import ClientCreditEntry
from app.domain.studio.finances.entities.payment import Payment
from app.domain.studio.finances.enums.client_credit_source_type import (
    ClientCreditSourceType,
)
from app.domain.studio.finances.enums.payment_enums import PaymentMethodType
from app.domain.studio.users.entities.user import User
from app.domain.studio.value_objects.client_code import ClientCode
from app.domain.studio.users.entities.vip_client import VipClient
from tests.fakes.fake_appointments_repository import FakeAppointmentsRepository
from tests.fakes.fake_client_credit_entries_repository import (
    FakeClientCreditEntriesRepository,
)
from tests.fakes.fake_email_service import FakeEmailService
from tests.fakes.fake_payments_repository import FakePaymentsRepository
from tests.fakes.fake_read_unit_of_work import FakeReadUnitOfWork
from tests.fakes.fake_users_repository import FakeUsersRepository
from app.core.config import settings
from tests.fakes.fake_vip_clients_repository import FakeVipClientsRepository
from tests.fakes.fake_write_unit_of_work import FakeWriteUnitOfWork


@pytest.fixture
def shared_users_repo():
    return FakeUsersRepository()


@pytest.fixture
def shared_vip_clients_repo():
    return FakeVipClientsRepository()


@pytest.fixture
def shared_client_credit_entries_repo():
    return FakeClientCreditEntriesRepository()


@pytest.fixture
def shared_appointments_repo():
    return FakeAppointmentsRepository()


@pytest.fixture
def shared_payments_repo():
    return FakePaymentsRepository()


@pytest.fixture
def read_uow(
    shared_users_repo,
    shared_vip_clients_repo,
    shared_client_credit_entries_repo,
    shared_appointments_repo,
    shared_payments_repo,
):
    uow = FakeReadUnitOfWork()
    uow.users = shared_users_repo
    uow.vip_clients = shared_vip_clients_repo
    uow.client_credit_entries = shared_client_credit_entries_repo
    uow.appointments = shared_appointments_repo
    uow.payments = shared_payments_repo
    return uow


@pytest.fixture
def write_uow(
    shared_users_repo,
    shared_vip_clients_repo,
    shared_client_credit_entries_repo,
    shared_appointments_repo,
    shared_payments_repo,
):
    uow = FakeWriteUnitOfWork()
    uow.users = shared_users_repo
    uow.vip_clients = shared_vip_clients_repo
    uow.client_credit_entries = shared_client_credit_entries_repo
    uow.appointments = shared_appointments_repo
    uow.payments = shared_payments_repo
    return uow


@pytest.fixture
def make_user():
    def _factory(**kwargs):
        return User(
            id=uuid4(),
            username=kwargs.get("username", "JhonDoe"),
            email=kwargs.get("email", "jhon@doe.com"),
            hashed_password=kwargs.get("hashed_password", hash_password("123456")),
            is_active=kwargs.get("is_active", True),
            is_admin=kwargs.get("is_admin", False),
            activation_token_version=kwargs.get("activation_token_version", 0),
            has_activated_once=kwargs.get("has_activated_once", False),
            password_token_version=kwargs.get("password_token_version", 0),
            access_token_version=kwargs.get("access_token_version", 0),
            refresh_token_version=kwargs.get("refresh_token_version", 0),
        )

    return _factory


@pytest.fixture
def make_token():
    def _factory(user, version=None, minutes=60, token_type="access"):
        if version is None:
            if token_type == "access":
                version = user.access_token_version
            else:
                version = user.refresh_token_version
        return jwt_service.create(
            subject=str(user.id),
            minutes=minutes,
            token_type=token_type,
            extra_claims={"ver": version},
        )

    return _factory


@pytest.fixture
def jwt_service_instance():
    return JWTService(secret_key=settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def access_token_service(jwt_service_instance):
    return VersionedTokenService(
        jwt_service_instance, token_type="access", ttl_minutes=60
    )


@pytest.fixture
def refresh_token_service(jwt_service_instance):
    return VersionedTokenService(
        jwt_service_instance, token_type="refresh", ttl_minutes=60
    )


@pytest.fixture
def make_vip_client():
    def _factory(**kwargs):
        return VipClient(
            id=uuid4(),
            first_name=kwargs.get("first_name", "Jhon"),
            last_name=kwargs.get("last_name", "Doe"),
            email=kwargs.get("email", "jhon@doe.com"),
            phone=kwargs.get("phone", "71999999999"),
            client_code=ClientCode(kwargs.get("client_code", "JHON-BLUE")),
        )

    return _factory


@pytest.fixture
def make_client_credit_entry():

    def _factory(**kwargs):

        source_type = kwargs.get(
            "source_type",
            ClientCreditSourceType.INDICATION,
        )

        vip_client_id = kwargs.get("vip_client_id", uuid4())
        source_id = kwargs.get("source_id", uuid4())
        quantity = kwargs.get("quantity", 10)
        reason = kwargs.get("reason", "test reason")
        created_at = kwargs.get("created_at")

        if source_type == ClientCreditSourceType.INDICATION:
            return ClientCreditEntry.create_indication(
                vip_client_id=vip_client_id,
                appointment_id=source_id,
                quantity=quantity,
                created_at=created_at,
            )

        if source_type == ClientCreditSourceType.ADDED_BY_ADMIN:
            return ClientCreditEntry.added_by_admin(
                vip_client_id=vip_client_id,
                admin_id=source_id,
                quantity=quantity,
                reason=reason,
                created_at=created_at,
            )

        if source_type == ClientCreditSourceType.USED_IN_APPOINTMENT:
            return ClientCreditEntry.used_in_appointment(
                vip_client_id=vip_client_id,
                appointment_id=source_id,
                quantity=quantity,
                created_at=created_at,
            )

        if source_type == ClientCreditSourceType.REVERSED_BY_ADMIN:
            return ClientCreditEntry.reverse(
                vip_client_id=vip_client_id,
                admin_id=source_id,
                original_entry_id=kwargs.get("related_entry_id", uuid4()),
                quantity=quantity,
                reason=reason,
                created_at=created_at,
            )

    return _factory


@pytest.fixture
def fake_email_service():
    return FakeEmailService()


@pytest.fixture
def fake_event_bus(fake_email_service):
    return setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service,
    )


@pytest.fixture
def make_payment():
    def _factory(**kwargs):
        base_now = kwargs.get(
            "base_now", datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
        )
        return Payment(
            id=uuid4(),
            amount=kwargs.get("amount", Decimal("10")),
            payment_method=kwargs.get("payment_method", PaymentMethodType.PIX),
            appointment_id=kwargs.get("appointment_id", uuid4()),
            vip_client_id=kwargs.get("vip_client_id", uuid4()),
            description=kwargs.get("description", "Pagamento da tatuagem"),
            external_reference=kwargs.get("external_reference", f"ref-{uuid4()}"),
            created_at=kwargs.get("created_at", base_now),
        )

    return _factory


@pytest.fixture
def make_appointment_base():
    def _factory(**kwargs):
        base_now = kwargs.get(
            "base_now", datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
        )

        start_at = kwargs.get(
            "start_at", base_now + timedelta(days=7, hours=3)
        )  # 13h of january 1st 2026

        end_at = kwargs.get(
            "end_at", base_now + timedelta(days=7, hours=6)
        )  # 16h of january 1st 2026

        return Appointment(
            id=kwargs.get("id", uuid4()),
            status=AppointmentStatus.REQUESTED,
            appointment_type=kwargs.get("appointment_type", AppointmentType.TATTOO),
            start_at=start_at,
            end_at=end_at,
            placement=kwargs.get("placement", "ombro-cotovelo"),
            details=kwargs.get("details", "tattoo de um dragão"),
            size=kwargs.get("size", "30cm"),
            current_session=kwargs.get("current_session", None),
            total_sessions=kwargs.get("total_sessions", None),
            color=kwargs.get("color", False),
            price=None,
            deposit_confirmed_at=None,
            client_info=kwargs.get(
                "client_info",
                ClientInfo(
                    vip_client_id=None,
                    email="client@email.com",
                    phone="71988888888",
                    name="Jhon Doe",
                ),
            ),
            referral_code=kwargs.get("referral_code", None),
            is_posted_on_socials=kwargs.get("is_posted_on_socials", False),
            observations=kwargs.get("observations", None),
        )

    return _factory


@pytest.fixture
def make_quoted_appointment(make_appointment_base):
    def _factory(**kwargs):
        base_now = kwargs.pop("base_now", datetime(2030, 1, 1, tzinfo=timezone.utc))

        appointment = make_appointment_base(base_now=base_now, **kwargs)
        appointment.quote(kwargs.get("price", Decimal("700")))
        return appointment

    return _factory


@pytest.fixture
def make_scheduled_appointment(make_quoted_appointment):
    def _factory(**kwargs):
        appointment = make_quoted_appointment(**kwargs)
        appointment.confirm_deposit()

        return appointment

    return _factory


@pytest.fixture
def make_completed_appointment(make_scheduled_appointment):
    def _factory(**kwargs):
        appointment = make_scheduled_appointment(**kwargs)
        appointment.complete(kwargs.get("total_paid", appointment.price))
        return appointment

    return _factory

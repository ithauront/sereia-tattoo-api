from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from tests.fakes.fake_appointments_repository import FakeAppointmentsRepository
from tests.fakes.fake_audit_logs_repository import FakeAuditLogsRepository
from tests.fakes.fake_calendar_settings_repository import FakeCalendarSettingsRepository
from tests.fakes.fake_client_credit_entries_repository import (
    FakeClientCreditEntriesRepository,
)
from tests.fakes.fake_payments_repository import FakePaymentsRepository
from tests.fakes.fake_refunds_repository import FakeRefundsRepository
from tests.fakes.fake_users_repository import FakeUsersRepository
from tests.fakes.fake_vip_clients_repository import FakeVipClientsRepository


class FakeReadUnitOfWork(ReadUnitOfWork):
    def __init__(self):
        self.users = FakeUsersRepository()
        self.vip_clients = FakeVipClientsRepository()
        self.client_credit_entries = FakeClientCreditEntriesRepository()
        self.appointments = FakeAppointmentsRepository()
        self.payments = FakePaymentsRepository()
        self.audit_logs = FakeAuditLogsRepository()
        self.refunds = FakeRefundsRepository()
        self.calendar_settings = FakeCalendarSettingsRepository()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

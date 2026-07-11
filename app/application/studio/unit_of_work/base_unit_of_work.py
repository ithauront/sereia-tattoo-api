from abc import ABC

from app.application.studio.repositories.appointments_repository import (
    AppointmentsRepository,
)
from app.application.studio.repositories.audit_logs_repository import AuditLogsRepository
from app.application.studio.repositories.calendar_exceptions_repository import (
    CalendarExceptionsRepository,
)
from app.application.studio.repositories.calendar_settings_repository import CalendarSettingsRepository
from app.application.studio.repositories.client_credit_entries_repository import (
    ClientCreditEntriesRepository,
)
from app.application.studio.repositories.payments_repository import PaymentsRepository
from app.application.studio.repositories.refunds_repository import RefundsRepository
from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.repositories.vip_clients_repository import (
    VipClientsRepository,
)


class BaseUnitOfWork(ABC):
    users: UsersRepository
    vip_clients: VipClientsRepository
    client_credit_entries: ClientCreditEntriesRepository
    payments: PaymentsRepository
    appointments: AppointmentsRepository
    audit_logs: AuditLogsRepository
    refunds: RefundsRepository
    calendar_settings: CalendarSettingsRepository
    calendar_exceptions: CalendarExceptionsRepository

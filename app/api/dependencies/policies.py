from app.domain.studio.appointments.policies.appointment_authorization_policy import (
    AppointmentAuthorizationPolicy,
)
from app.domain.studio.appointments.policies.appointment_project_policy import (
    AppointmentProjectPolicy,
)
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)
from app.domain.studio.appointments.policies.deposit_policy import DepositPolicy


def get_calendar_policy():
    return CalendarAvailabilityPolicy()


def get_appointment_project_policy():
    return AppointmentProjectPolicy()


def get_appointment_authorization_policy():
    return AppointmentAuthorizationPolicy()


def get_deposit_policy():
    return DepositPolicy()

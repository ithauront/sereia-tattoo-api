from app.domain.studio.appointments.policies.appointment_authorization_policy import (
    AppointmentAuthorizationPolicy,
)
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)


def get_calendar_policy():
    return CalendarAvailabilityPolicy()


def get_appointment_authorization_policy():
    return AppointmentAuthorizationPolicy()

from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)


def get_calendar_policy():
    return CalendarAvailabilityPolicy()

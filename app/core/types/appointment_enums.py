from enum import Enum


class AppointmentType(str, Enum):
    TATTOO = "tattoo"
    PIERCING = "piercing"


class AppointmentStatus(str, Enum):
    REQUESTED = "requested"
    QUOTED = "quoted"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELED = "canceled"

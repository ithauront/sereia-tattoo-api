from uuid import UUID

from pydantic import BaseModel


class CompletePaidAppointmentInput(BaseModel):
    appointment_id: UUID
    actor_id: UUID

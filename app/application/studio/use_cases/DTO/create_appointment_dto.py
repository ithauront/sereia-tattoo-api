from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.types.appointment_enums import AppointmentType
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.value_objects.client_code import ClientCode

"""
TODO: Quando formos fazer a rota de create appointment a gente precisara receber 
os dados de clientInfo
soltos e la a gente vai criar o valueObject clientinfo
assim:
    vip_client_id: UUID | None

    name: str | None

    email: str | None

    phone: str | None

    e na rota a gente transforma isso em:
    client_info = ClientInfo(
    vip_client_id=request.vip_client_id,
    name=request.name,
    email=request.email,
    phone=request.phone,
)
e provavelmente faremos o mesmo com o clientCode

"""


@dataclass(frozen=True)
class CreateAppointmentInput:
    appointment_type: AppointmentType
    user_id: UUID
    start_at: datetime
    end_at: datetime
    placement: str
    details: str
    client_info: ClientInfo
    size: str | None = None
    color: bool = False

    referral_code: ClientCode | None = None

    actor_id: UUID | None = None

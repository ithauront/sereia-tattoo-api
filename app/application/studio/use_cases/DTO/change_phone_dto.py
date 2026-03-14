from uuid import UUID

from pydantic import BaseModel


class ChangeVipClientPhoneInput(BaseModel):
    vip_client_id: UUID
    new_phone: str

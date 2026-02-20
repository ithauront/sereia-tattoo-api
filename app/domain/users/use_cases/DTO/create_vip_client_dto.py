from pydantic import BaseModel, EmailStr


class CreateVipClientInput(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    client_code: str

from uuid import UUID
from app.domain.studio.value_objects.client_code import ClientCode
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo


class AppointmentCompleted:
    def __init__(self,appointment_id:UUID, referral_code:ClientCode,  client_info: ClientInfo):
        self.referral_code = referral_code
        self.appointment_id = appointment_id
        self.client_info = client_info

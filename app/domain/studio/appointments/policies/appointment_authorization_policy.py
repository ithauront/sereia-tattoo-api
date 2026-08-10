from app.core.exceptions.appointments import OnlyAdminOrOwnerOfAppointmentError
from app.domain.studio.appointments.entities.appointment import Appointment
from app.domain.studio.users.entities.user import User


class AppointmentAuthorizationPolicy:
    def ensure_admin_or_owner(self, actor: User, appointment: Appointment) -> None:

        is_owner = appointment.user_id == actor.id
        is_admin = actor.is_admin

        if not (is_owner or is_admin):
            raise OnlyAdminOrOwnerOfAppointmentError()

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from app.application.studio.repositories.appointments_repository import (
    AppointmentsRepository,
)
from app.application.studio.use_cases.DTO.client_filters import ClientInfoFilter
from app.application.studio.use_cases.DTO.commun import Direction
from app.domain.studio.appointments.entities.appointment import Appointment
from app.core.types.appointment_enums import (
    AppointmentStatus,
    AppointmentType,
)
from app.domain.studio.value_objects.client_code import ClientCode


class FakeAppointmentsRepository(AppointmentsRepository):
    def __init__(self):
        self._appointments: List[Appointment] = []

    def create(self, appointment: Appointment) -> None:
        self._appointments.append(appointment)

    def update(self, appointment: Appointment) -> None:
        for index, appointment_in_memory in enumerate(self._appointments):
            if appointment_in_memory.id == appointment.id:
                appointment.updated_at = datetime.now(timezone.utc)
                self._appointments[index] = appointment
                return

    def find_by_id(self, appointment_id: UUID) -> Optional[Appointment]:
        for appointment_in_memory in self._appointments:
            if appointment_in_memory.id == appointment_id:
                return appointment_in_memory
        return None

    def find_many(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        status: AppointmentStatus | None = None,
        appointment_type: AppointmentType | None = None,
        client_info: ClientInfoFilter | None = None,
        color: bool | None = None,
        is_posted_on_socials: bool | None = None,
        has_deposit: bool | None = None,
        referral_code: ClientCode | None = None,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[Appointment]:

        MAX_LIMIT = 5000
        limit = min(limit, MAX_LIMIT)

        filtered_appointments = self._filter_appointments(
            start_date=start_date,
            end_date=end_date,
            status=status,
            appointment_type=appointment_type,
            client_info=client_info,
            color=color,
            is_posted_on_socials=is_posted_on_socials,
            has_deposit=has_deposit,
            referral_code=referral_code,
        )

        order_appointments = self._apply_order(filtered_appointments, direction)
        paginated = order_appointments[offset : offset + limit]

        return paginated

    def count_many(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        status: AppointmentStatus | None = None,
        appointment_type: AppointmentType | None = None,
        client_info: ClientInfoFilter | None = None,
        color: bool | None = None,
        is_posted_on_socials: bool | None = None,
        has_deposit: bool | None = None,
        referral_code: ClientCode | None = None,
    ):
        filtered_appointments = self._filter_appointments(
            start_date=start_date,
            end_date=end_date,
            status=status,
            appointment_type=appointment_type,
            client_info=client_info,
            color=color,
            is_posted_on_socials=is_posted_on_socials,
            has_deposit=has_deposit,
            referral_code=referral_code,
        )

        return len(filtered_appointments)

    def _filter_appointments(
        self,
        *,
        start_date: datetime | None,
        end_date: datetime | None,
        status: AppointmentStatus | None,
        appointment_type: AppointmentType | None,
        client_info: ClientInfoFilter | None,
        color: bool | None,
        is_posted_on_socials: bool | None,
        has_deposit: bool | None,
        referral_code: ClientCode | None,
    ):
        filtered = list(self._appointments)

        if start_date is not None:
            filtered = [
                appointment
                for appointment in filtered
                if appointment.end_at >= start_date
            ]
        if end_date is not None:
            filtered = [
                appointment
                for appointment in filtered
                if appointment.start_at <= end_date
            ]

        if color is not None:
            filtered = [
                appointment for appointment in filtered if appointment.color == color
            ]
        if is_posted_on_socials is not None:
            filtered = [
                appointment
                for appointment in filtered
                if appointment.is_posted_on_socials == is_posted_on_socials
            ]

        if has_deposit is True:
            filtered = [
                appointment
                for appointment in filtered
                if appointment.deposit_confirmed_at is not None
            ]
        elif has_deposit is False:
            filtered = [
                appointment
                for appointment in filtered
                if appointment.deposit_confirmed_at is None
            ]

        if client_info is not None:
            if client_info.vip_client_id is not None:
                filtered = [
                    appointment
                    for appointment in filtered
                    if appointment.client_info.vip_client_id
                    == client_info.vip_client_id
                ]
            else:
                if client_info.email is not None:
                    filtered = [
                        appointment
                        for appointment in filtered
                        if appointment.client_info.email == client_info.email
                    ]
                if client_info.phone is not None:
                    filtered = [
                        appointment
                        for appointment in filtered
                        if appointment.client_info.phone == client_info.phone
                    ]

        if referral_code is not None:
            filtered = [
                appointment
                for appointment in filtered
                if appointment.referral_code == referral_code
            ]

        if status is not None:
            filtered = [
                appointment for appointment in filtered if appointment.status == status
            ]

        if appointment_type is not None:
            filtered = [
                appointment
                for appointment in filtered
                if appointment.appointment_type == appointment_type
            ]

        return filtered

    def _apply_order(self, appointments: List[Appointment], direction: Direction):
        reverse = direction == Direction.desc

        return sorted(
            appointments,
            key=lambda appointment: (appointment.created_at, appointment.id),
            reverse=reverse,
        )

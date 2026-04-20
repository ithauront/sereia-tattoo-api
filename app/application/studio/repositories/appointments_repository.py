from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.application.studio.use_cases.DTO.client_filters import ClientInfoFilter
from app.application.studio.use_cases.DTO.commun import Direction
from app.domain.studio.appointments.entities.appointment import Appointment
from app.domain.studio.appointments.enums.appointment_enums import (
    AppointmentStatus,
    AppointmentType,
)
from app.domain.studio.value_objects.client_code import ClientCode


class AppointmentsRepository(ABC):
    @abstractmethod
    def create(self, appointment: Appointment) -> None: ...

    @abstractmethod
    def update(self, appointment: Appointment) -> None: ...

    @abstractmethod
    def find_by_id(self, appointment_id: UUID) -> Optional[Appointment]: ...

    @abstractmethod
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
    ) -> List[Appointment]: ...

    @abstractmethod
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
    ) -> int: ...

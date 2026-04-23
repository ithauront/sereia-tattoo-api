from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.studio.repositories.appointments_repository import (
    AppointmentsRepository,
)
from app.application.studio.use_cases.DTO.client_filters import ClientInfoFilter
from app.application.studio.use_cases.DTO.commun import Direction
from app.domain.studio.appointments.entities.appointment import Appointment
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.appointments.enums.appointment_enums import (
    AppointmentStatus,
    AppointmentType,
)
from app.domain.studio.value_objects.client_code import ClientCode
from app.infrastructure.sqlalchemy.models.appointments import AppointmentModel


# TODO fazer fake e teste do fake e tambem teste do real
class SQLAlchemyAppointmentsRepository(AppointmentsRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, appointment: Appointment) -> None:
        orm_appointment = self._to_model(appointment)

        self.session.add(orm_appointment)
        self.session.flush()

    def find_by_id(self, appointment_id: UUID) -> Optional[Appointment]:
        appointment_in_question = select(AppointmentModel).where(
            AppointmentModel.id == appointment_id
        )
        orm_appointment = self.session.scalar(appointment_in_question)

        if orm_appointment is None:
            return None

        return self._to_entity(orm_appointment)

    def update(self, appointment: Appointment) -> None:
        appointment_in_question = select(AppointmentModel).where(
            AppointmentModel.id == appointment.id
        )
        orm_appointment = self.session.scalar(appointment_in_question)

        if orm_appointment is None:
            return None

        if appointment.client_info.vip_client_id:
            orm_appointment.vip_client_id = appointment.client_info.vip_client_id
            orm_appointment.client_name = None
            orm_appointment.client_email = None
            orm_appointment.client_phone = None
        else:
            orm_appointment.vip_client_id = None
            orm_appointment.client_name = appointment.client_info.name
            orm_appointment.client_email = appointment.client_info.email
            orm_appointment.client_phone = appointment.client_info.phone

        orm_appointment.referral_code = (
            str(appointment.referral_code)
            if appointment.referral_code is not None
            else None
        )

        orm_appointment.status = appointment.status
        orm_appointment.appointment_type = appointment.appointment_type
        orm_appointment.start_at = appointment.start_at
        orm_appointment.end_at = appointment.end_at
        orm_appointment.placement = appointment.placement
        orm_appointment.details = appointment.details
        orm_appointment.size = appointment.size
        orm_appointment.current_session = appointment.current_session
        orm_appointment.total_sessions = appointment.total_sessions
        orm_appointment.color = appointment.color
        orm_appointment.price = appointment.price
        orm_appointment.deposit_confirmed_at = appointment.deposit_confirmed_at
        orm_appointment.is_posted_on_socials = appointment.is_posted_on_socials
        orm_appointment.observations = appointment.observations
        orm_appointment.updated_at = appointment.updated_at

        self.session.flush()

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

        filters = self._build_filters(
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

        appointments_in_question = select(AppointmentModel).where(*filters)

        appointments_in_question = self._apply_order(
            appointments_in_question, direction=direction
        )
        appointments_in_question = appointments_in_question.limit(limit).offset(offset)

        return [
            self._to_entity(orm_appointment)
            for orm_appointment in self.session.scalars(appointments_in_question)
        ]

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
    ) -> int:
        filters = self._build_filters(
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
        total = select(func.count(AppointmentModel.id)).where(*filters)

        return self.session.scalar(total) or 0

    def _build_filters(
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
        filters = []

        if start_date is not None:
            filters.append(AppointmentModel.end_at >= start_date)
        if end_date is not None:
            filters.append(AppointmentModel.start_at <= end_date)

        if color is not None:
            filters.append(AppointmentModel.color == color)
        if is_posted_on_socials is not None:
            filters.append(
                AppointmentModel.is_posted_on_socials == is_posted_on_socials
            )

        if has_deposit is True:
            filters.append(AppointmentModel.deposit_confirmed_at.is_not(None))
        elif has_deposit is False:
            filters.append(AppointmentModel.deposit_confirmed_at.is_(None))

        if client_info is not None:
            if client_info.vip_client_id is not None:
                filters.append(
                    AppointmentModel.vip_client_id == client_info.vip_client_id
                )
            else:
                if client_info.email is not None:
                    filters.append(AppointmentModel.client_email == client_info.email)
                if client_info.phone is not None:
                    filters.append(AppointmentModel.client_phone == client_info.phone)

        if referral_code is not None:
            filters.append(AppointmentModel.referral_code == str(referral_code))

        if status is not None:
            filters.append(AppointmentModel.status == status)

        if appointment_type is not None:
            filters.append(AppointmentModel.appointment_type == appointment_type)

        return filters

    def _to_model(self, appointment: Appointment) -> AppointmentModel:
        if appointment.client_info.vip_client_id:
            vip_client_id = appointment.client_info.vip_client_id
            client_name = None
            client_email = None
            client_phone = None
        else:
            vip_client_id = None
            client_name = appointment.client_info.name
            client_email = appointment.client_info.email
            client_phone = appointment.client_info.phone

        referral_code = (
            str(appointment.referral_code)
            if appointment.referral_code is not None
            else None
        )

        return AppointmentModel(
            id=appointment.id,
            status=appointment.status,
            appointment_type=appointment.appointment_type,
            start_at=appointment.start_at,
            end_at=appointment.end_at,
            placement=appointment.placement,
            details=appointment.details,
            size=appointment.size,
            current_session=appointment.current_session,
            total_sessions=appointment.total_sessions,
            color=appointment.color,
            price=appointment.price,
            deposit_confirmed_at=appointment.deposit_confirmed_at,
            vip_client_id=vip_client_id,
            client_name=client_name,
            client_email=client_email,
            client_phone=client_phone,
            referral_code=referral_code,
            is_posted_on_socials=appointment.is_posted_on_socials,
            observations=appointment.observations,
            created_at=appointment.created_at,
            updated_at=appointment.updated_at,
        )

    def _to_entity(self, orm_appointment: AppointmentModel) -> Appointment:

        if orm_appointment.vip_client_id:
            client_info = ClientInfo(
                vip_client_id=orm_appointment.vip_client_id,
                name=None,
                email=None,
                phone=None,
            )
        else:
            client_info = ClientInfo(
                name=orm_appointment.client_name,
                email=orm_appointment.client_email,
                phone=orm_appointment.client_phone,
                vip_client_id=None,
            )

        client_code = (
            ClientCode(orm_appointment.referral_code)
            if orm_appointment.referral_code is not None
            else None
        )

        return Appointment(
            id=UUID(str(orm_appointment.id)),
            appointment_type=orm_appointment.appointment_type,
            status=orm_appointment.status,
            start_at=orm_appointment.start_at,
            end_at=orm_appointment.end_at,
            placement=orm_appointment.placement,
            details=orm_appointment.details,
            size=orm_appointment.size,
            current_session=orm_appointment.current_session,
            total_sessions=orm_appointment.total_sessions,
            color=orm_appointment.color,
            price=orm_appointment.price,
            deposit_confirmed_at=orm_appointment.deposit_confirmed_at,
            client_info=client_info,
            referral_code=client_code,
            is_posted_on_socials=orm_appointment.is_posted_on_socials,
            observations=orm_appointment.observations,
            created_at=orm_appointment.created_at,
            updated_at=orm_appointment.updated_at,
        )

    def _apply_order(self, query, direction: Direction):
        if direction == Direction.asc:
            return query.order_by(
                AppointmentModel.created_at.asc(),
                AppointmentModel.id.asc(),
            )
        return query.order_by(
            AppointmentModel.created_at.desc(),
            AppointmentModel.id.desc(),
        )

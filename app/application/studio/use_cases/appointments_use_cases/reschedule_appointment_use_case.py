from datetime import datetime, timezone

from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.reschedule_appointment_dto import (
    RescheduleAppointmentInput,
    RescheduleAppointmentOutput,
)
from app.core.exceptions.appointments import (
    AppointmentMustHaveRealisticTimeAndDateError,
    AppointmentNotFoundError,
    IncorrectAppointmentStatusError,
    ReasonForDepositRetentionOverrideMustBeProvidedError,
    SlotIsAlreadyOccupiedError,
)
from app.core.exceptions.calendar import CannotFindWorkingPeriodsForThisUserError
from app.core.types.appointment_enums import AppointmentStatus
from app.core.types.audit_actor_type import AuditActorType
from app.core.types.payment_enums import PaymentAllocationStatus, PaymentPurposeType
from app.core.validations.text import validate_text
from app.domain.studio.appointments.entities.appointment import Appointment
from app.domain.studio.appointments.policies.appointment_authorization_policy import (
    AppointmentAuthorizationPolicy,
)
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)
from app.domain.studio.appointments.policies.deposit_policy import DepositPolicy
from app.domain.studio.finances.entities.payment import Payment


class RescheduleAppointmentUseCase:
    def __init__(
        self,
        write_uow: WriteUnitOfWork,
        read_uow: ReadUnitOfWork,
        calendar_policy: CalendarAvailabilityPolicy,
        deposit_policy: DepositPolicy,
        authorization_policy: AppointmentAuthorizationPolicy,
        integration_bus: IntegrationEventBus,
    ):
        self.write_uow = write_uow
        self.read_uow = read_uow
        self.calendar_policy = calendar_policy
        self.deposit_policy = deposit_policy
        self.authorization_policy = authorization_policy
        self.integration_bus = integration_bus

    async def execute(self, data: RescheduleAppointmentInput) -> RescheduleAppointmentOutput:
        with self.write_uow:
            appointment = self._get_authorized_appointment(data)
            override_reason = self._validate_override_reason(data)
            now = datetime.now(timezone.utc)
            if data.start_at <= now or data.end_at <= data.start_at:
                raise AppointmentMustHaveRealisticTimeAndDateError()
            self._ensure_calendar_available(appointment, data)

            if appointment.start_at == data.start_at and appointment.end_at == data.end_at:
                return self._build_output(appointment)

            previous = (appointment.start_at, appointment.end_at, appointment.status)
            payments = self.write_uow.payments.find_many_by_appointment_id(appointment.id)
            retention_required = (
                appointment.deposit_confirmed_at is not None
                and not self.deposit_policy.is_deposit_transferable_on_reschedule(
                    appointment=appointment, payments=payments, reschedule_at=now
                )
            )
            override_applied = retention_required and data.override_deposit_retention
            retained_payment_ids = []
            if retention_required and not data.override_deposit_retention:
                retained_payment_ids = self._retain_deposits(appointment, payments, now)

            event = appointment.reschedule(
                new_start_at=data.start_at,
                new_end_at=data.end_at,
                was_deposit_retained=bool(retained_payment_ids),
            )
            self.write_uow.appointments.update(appointment=appointment)
            self._record_audit(
                appointment=appointment,
                data=data,
                previous=previous,
                retained_payment_ids=retained_payment_ids,
                override_reason=override_reason,
                override_applied=override_applied,
                now=now,
            )
            result = self._build_output(
                appointment,
                was_deposit_retained=bool(retained_payment_ids),
                override_applied=override_applied,
            )

        if event is not None:
            await self.integration_bus.publish(event, uow=self.read_uow)
        return result

    def _get_authorized_appointment(self, data: RescheduleAppointmentInput) -> Appointment:
        appointment = self.write_uow.appointments.find_by_id(data.appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError()
        self.authorization_policy.ensure_admin_or_owner(actor=data.actor, appointment=appointment)
        if appointment.status in (AppointmentStatus.CANCELED, AppointmentStatus.COMPLETED):
            raise IncorrectAppointmentStatusError()

        return appointment

    @staticmethod
    def _validate_override_reason(data: RescheduleAppointmentInput) -> str | None:
        if not data.override_deposit_retention:
            return None
        reason = (data.deposit_override_reason or "").strip()
        if not reason:
            raise ReasonForDepositRetentionOverrideMustBeProvidedError()
        return validate_text(reason)

    def _ensure_calendar_available(
        self, appointment: Appointment, data: RescheduleAppointmentInput
    ) -> None:
        calendar_owner_id = appointment.user_id

        calendar_of_user = self.write_uow.calendar_settings.find_by_user_id(calendar_owner_id)

        if not calendar_of_user:
            raise CannotFindWorkingPeriodsForThisUserError()

        calendar_exceptions_overlap = self.write_uow.calendar_exceptions.find_overlap(
            user_id=calendar_owner_id,
            start_at=data.start_at,
            end_at=data.end_at,
        )

        occupied_slots = self.write_uow.appointments.find_overlap(
            start_date=data.start_at,
            end_date=data.end_at,
            user_id=appointment.user_id,
            exclude_appointment_id=appointment.id,
        )
        if occupied_slots:
            raise SlotIsAlreadyOccupiedError()

        self.calendar_policy.can_reschedule(
            calendar_settings=calendar_of_user,
            calendar_exceptions=calendar_exceptions_overlap,
            # execute already required admin or calendar owner; other checks still apply.
            can_ignore_booking_window=True,
            new_start_at=data.start_at,
            new_end_at=data.end_at,
        )

    def _retain_deposits(
        self, appointment: Appointment, payments: list[Payment], now: datetime
    ) -> list[str]:
        appointment.invalidate_deposit()
        retained_payment_ids = []
        for payment in payments:
            if (
                payment.payment_purpose == PaymentPurposeType.DEPOSIT
                and payment.allocation_status == PaymentAllocationStatus.ACTIVE
            ):
                payment.retain_deposit(
                    retained_at=now,
                    reason="Caução retida porque o reagendamento não cumpriu o prazo mínimo exigido",
                )
                self.write_uow.payments.update_allocation_status(payment=payment)
                retained_payment_ids.append(str(payment.id))
        return retained_payment_ids

    def _record_audit(
        self,
        appointment: Appointment,
        data: RescheduleAppointmentInput,
        previous: tuple[datetime, datetime, AppointmentStatus],
        retained_payment_ids: list[str],
        override_reason: str | None,
        override_applied: bool,
        now: datetime,
    ) -> None:
        old_start_at, old_end_at, old_status = previous
        log = AuditLogEntry(
            entity_name="appointments",
            entity_id=appointment.id,
            action="reschedule appointment",
            actor_id=data.actor.id,
            actor_type=AuditActorType.USER,
            changes={
                "old_start_at": old_start_at.isoformat(),
                "old_end_at": old_end_at.isoformat(),
                "new_start_at": appointment.start_at.isoformat(),
                "new_end_at": appointment.end_at.isoformat(),
                "old_status": old_status.value,
                "new_status": appointment.status.value,
                "was_deposit_retained": bool(retained_payment_ids),
                "retained_payment_ids": retained_payment_ids,
                # Solicitar a exceção não significa que ela foi necessária (ex.: prazo >= 48h).
                "deposit_retention_override_requested": data.override_deposit_retention,
                "deposit_retention_override_applied": override_applied,
                "deposit_retention_override_reason": override_reason,
            },
            performed_at=now,
        )

        self.write_uow.audit_logs.create(log)

    @staticmethod
    def _build_output(
        appointment: Appointment,
        was_deposit_retained: bool = False,
        override_applied: bool = False,
    ) -> RescheduleAppointmentOutput:
        return RescheduleAppointmentOutput(
            appointment_id=appointment.id,
            start_at=appointment.start_at,
            end_at=appointment.end_at,
            status=appointment.status,
            was_deposit_retained=was_deposit_retained,
            deposit_override_applied=override_applied,
        )

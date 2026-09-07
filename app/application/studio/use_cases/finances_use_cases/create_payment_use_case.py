from datetime import datetime, timezone
from uuid import UUID

from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.event_bus.transactional_event_bus import TransactionalEventBus
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.payment_dto import CreatePaymentInput, CreatePaymentOutput
from app.core.exceptions.appointments import (
    AppointmentClientInfoBreakingDomainRules,
    AppointmentNotFoundError,
    IncorrectAppointmentStatusError,
)
from app.core.exceptions.payment import (
    DuplicateExternalReferenceError,
    IdempotencyKeyConflictError,
    PaymentOfThisPurposeMustHaveAppointmentError,
    PaymentOfThisTypeDoesNotNeedAVipClient,
    VipClientHasInsufficientCreditError,
    VipClientIdIsRequiredError,
)
from app.core.exceptions.users import VipClientNotFoundError
from app.core.types.appointment_enums import AppointmentStatus
from app.core.types.audit_actor_type import AuditActorType
from app.core.types.payment_enums import PaymentMethodType, PaymentPurposeType
from app.domain.studio.appointments.entities.appointment import Appointment
from app.domain.studio.finances.entities.client_credit_entry import ClientCreditEntry
from app.domain.studio.finances.entities.payment import Payment
from app.domain.studio.finances.events.send_deposit_confirmation_email import (
    SendDepositConfirmationEmailEvent,
)
from app.domain.studio.finances.policies.client_credit_conversion_policy import (
    ClientCreditConversionPolicy,
)
from app.domain.studio.users.entities.vip_client import VipClient


class CreatePaymentUseCase:
    def __init__(
        self,
        uow: WriteUnitOfWork,
        transactional_event_bus: TransactionalEventBus,
        integration_event_bus: IntegrationEventBus,
    ):
        self.uow = uow
        self.transactional_event_bus = transactional_event_bus
        self.integration_event_bus = integration_event_bus

    async def execute(self, data: CreatePaymentInput) -> CreatePaymentOutput:
        deposit_confirmation_email_event = None

        with self.uow:
            existing_payment = self._payment_already_exists(data)
            if existing_payment is not None:
                return existing_payment

            self._ensure_external_reference_is_available(data.external_reference)

            appointment = self._get_appointment_if_required(
                appointment_id=data.appointment_id, purpose=data.payment_purpose
            )
            if (
                data.payment_method != PaymentMethodType.CLIENT_CREDIT
                and data.credit_owner_vip_client_id is not None
            ):
                raise PaymentOfThisTypeDoesNotNeedAVipClient()

            vip_client = self._get_credit_owner_for_update(data)

            payment = Payment.create(
                id=data.idempotency_key,
                amount=data.amount,
                payment_method=data.payment_method,
                payment_purpose=data.payment_purpose,
                vip_client_id=vip_client.id if vip_client else None,
                appointment_id=data.appointment_id,
                external_reference=data.external_reference,
                description=data.description,
            )

            deducted_client_credit = None
            if vip_client is not None:
                credits_to_consume = ClientCreditConversionPolicy.credits_to_consume(payment.amount)
                self._validate_credit_balance(
                    vip_client=vip_client,
                    credits_to_consume=credits_to_consume,
                )
                deducted_client_credit = ClientCreditEntry.used_as_payment(
                    vip_client_id=vip_client.id,
                    payment_id=payment.id,
                    quantity=credits_to_consume,
                )

            self.uow.payments.create(payment)
            if deducted_client_credit is not None:
                self.uow.client_credit_entries.create(deducted_client_credit)

            log_payment, log_client_credit = self._create_audit_logs(
                actor_id=data.actor.id, payment=payment, deducted_client_credit=deducted_client_credit
            )
            self.uow.audit_logs.create(log_payment)
            if log_client_credit is not None:
                self.uow.audit_logs.create(log_client_credit)

            if data.payment_purpose == PaymentPurposeType.DEPOSIT:
                event = self._get_deposit_event(appointment=appointment, payment=payment)
                await self.transactional_event_bus.publish(event, uow=self.uow)
                deposit_confirmation_email_event = self._get_deposit_confirmation_email_event(
                    appointment=appointment,
                    payment=payment,
                )

        if deposit_confirmation_email_event is not None:
            await self.integration_event_bus.publish(deposit_confirmation_email_event)

        return self._to_output(payment)

    @staticmethod
    def _to_output(payment: Payment) -> CreatePaymentOutput:
        return CreatePaymentOutput(
            payment_id=payment.id,
            appointment_id=payment.appointment_id,
            amount=payment.amount,
            payment_method=payment.payment_method,
            payment_purpose=payment.payment_purpose,
            vip_client_id=payment.vip_client_id,
            created_at=payment.created_at,
        )

    def _payment_already_exists(self, data: CreatePaymentInput) -> CreatePaymentOutput | None:
        payment = self.uow.payments.find_by_id(data.idempotency_key)
        if payment is None:
            return None
        if not payment.matches_creation_request(
            amount=data.amount,
            payment_method=data.payment_method,
            payment_purpose=data.payment_purpose,
            vip_client_id=data.credit_owner_vip_client_id,
            appointment_id=data.appointment_id,
            external_reference=data.external_reference,
            description=data.description,
        ):
            raise IdempotencyKeyConflictError()
        return self._to_output(payment)

    def _ensure_external_reference_is_available(self, external_reference: str | None) -> None:
        if external_reference is None:
            return
        if self.uow.payments.exists_by_external_reference(external_reference):
            raise DuplicateExternalReferenceError()

    def _get_appointment_if_required(
        self, *, purpose: PaymentPurposeType, appointment_id: UUID | None
    ) -> Appointment | None:
        if appointment_id is None:
            if purpose in (PaymentPurposeType.APPOINTMENT, PaymentPurposeType.DEPOSIT):
                raise PaymentOfThisPurposeMustHaveAppointmentError()
            return None

        appointment = self.uow.appointments.find_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError()

        return appointment

    def _create_audit_logs(
        self,
        *,
        actor_id: UUID,
        payment: Payment,
        deducted_client_credit: ClientCreditEntry | None,
    ) -> tuple[AuditLogEntry, AuditLogEntry | None]:

        payment_log = AuditLogEntry(
            entity_name="payments",
            entity_id=payment.id,
            action="create payment",
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            changes={
                "creation_state_must_important_info": {
                    "payment_amount": str(payment.amount),
                    "payment_method": payment.payment_method.value,
                    "description": payment.description,
                    "purpose": payment.payment_purpose.value,
                    "appointment_reference": str(payment.appointment_id)
                    if payment.appointment_id
                    else None,
                    "vip_client_id": str(payment.vip_client_id) if payment.vip_client_id else None,
                    "external_reference": payment.external_reference,
                }
            },
            performed_at=datetime.now(timezone.utc),
        )

        client_credit_log = None

        if deducted_client_credit is not None:
            client_credit_log = AuditLogEntry(
                entity_name="client_credit_entry",
                entity_id=deducted_client_credit.id,
                action="deduct client credits",
                actor_id=actor_id,
                actor_type=AuditActorType.USER,
                changes={
                    "vip_client_id": str(deducted_client_credit.vip_client_id)
                    if deducted_client_credit.vip_client_id
                    else None,
                    "credits_deducted": str(abs(deducted_client_credit.quantity)),
                    "reason": f"used_as_payment in payment_id: {payment.id}",
                },
                performed_at=datetime.now(timezone.utc),
            )

        return payment_log, client_credit_log

    def _get_deposit_event(self, appointment: Appointment | None, payment: Payment):
        if appointment is None:
            raise PaymentOfThisPurposeMustHaveAppointmentError()

        if appointment.status != AppointmentStatus.QUOTED:
            raise IncorrectAppointmentStatusError()
        return payment.record_deposit_event()

    def _get_deposit_confirmation_email_event(
        self,
        *,
        appointment: Appointment | None,
        payment: Payment,
    ) -> SendDepositConfirmationEmailEvent:
        if appointment is None:
            raise PaymentOfThisPurposeMustHaveAppointmentError()

        client_email = appointment.client_info.email
        if client_email is None:
            vip_client_id = appointment.client_info.vip_client_id
            if vip_client_id is None:
                raise AppointmentClientInfoBreakingDomainRules()

            vip_client = self.uow.vip_clients.find_by_id(vip_client_id)
            if vip_client is None:
                raise AppointmentClientInfoBreakingDomainRules()
            client_email = vip_client.email

        return SendDepositConfirmationEmailEvent(
            client_email=client_email,
            amount=payment.amount,
            appointment_type=appointment.appointment_type,
            start_at=appointment.start_at,
        )

    def _get_credit_owner_for_update(
        self,
        data: CreatePaymentInput,
    ) -> VipClient | None:
        if data.payment_method != PaymentMethodType.CLIENT_CREDIT:
            return None

        if data.credit_owner_vip_client_id is None:
            raise VipClientIdIsRequiredError()

        vip_client = self.uow.vip_clients.find_by_id_for_update(data.credit_owner_vip_client_id)

        if vip_client is None:
            raise VipClientNotFoundError()

        return vip_client

    def _validate_credit_balance(
        self,
        *,
        vip_client: VipClient,
        credits_to_consume: int,
    ) -> None:
        balance = self.uow.client_credit_entries.get_balance(vip_client_id=vip_client.id)

        if credits_to_consume > balance:
            raise VipClientHasInsufficientCreditError()

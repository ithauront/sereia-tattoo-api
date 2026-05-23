from app.domain.studio.appointments.events.appointment_completed import (
    AppointmentCompleted,
)
from app.core.types.payment_enums import PaymentMethodType
from decimal import Decimal
from app.domain.studio.finances.entities.client_credit_entry import ClientCreditEntry
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.core.types.audit_actor_type import AuditActorType
from app.core.types.client_credit_source_type import ClientCreditSourceType
from datetime import datetime, timezone
from math import ceil


class AddCreditsFromCompletedAppointmentHandler:
    def __init__(self, write_uow_factory):
        self.write_uow_factory = write_uow_factory

    async def handle(self, event: AppointmentCompleted) -> None:
        """In this handler silent returns prevent collateral
        credit generation failures from breaking the completed appointment flow."""
        with self.write_uow_factory() as uow:
            vip_client = uow.vip_clients.find_by_client_code(event.referral_code.value)
            if vip_client is None:

                return

            existing_entries = uow.client_credit_entries.find_many_by_source_id(
                source_id=event.appointment_id,
            )

            for entry in existing_entries:
                if (
                    entry.vip_client_id == vip_client.id
                    and entry.source_type == ClientCreditSourceType.INDICATION
                ):
                    return

            total_credits_before = uow.client_credit_entries.get_balance(
                vip_client_id=vip_client.id
            )

            payments = uow.payments.find_many_by_appointment_id(
                appointment_id=event.appointment_id
            )
            payments_in_money = [
                payment
                for payment in payments
                if payment.payment_method != PaymentMethodType.CLIENT_CREDIT
            ]

            total_in_money = sum(
                (payment.amount for payment in payments_in_money),
                Decimal("0"),
            )

            if total_in_money <= 0:
                return

            rate = (
                Decimal("0.05")
                if event.client_info.matches_vip(vip_client_id=vip_client.id)
                else Decimal("0.10")
            )

            quantity = ceil(total_in_money * rate)

            client_credits = ClientCreditEntry.create_indication(
                vip_client_id=vip_client.id,
                appointment_id=event.appointment_id,
                quantity=quantity,
            )

            uow.client_credit_entries.create(client_credit_entry=client_credits)

            total_credits_after = uow.client_credit_entries.get_balance(
                vip_client_id=vip_client.id
            )

            log = AuditLogEntry(
                entity_name="client_credit_entry",
                entity_id=client_credits.id,
                action="create credits from appointment done",
                actor_id=None,
                actor_type=AuditActorType.SYSTEM,
                changes={
                    "balance": {
                        "from": total_credits_before,
                        "to": total_credits_after,
                    },
                    "credit": {
                        "source_type": ClientCreditSourceType.INDICATION,
                        "quantity": quantity,
                    },
                    "vip_client": {
                        "id": vip_client.id,
                        "client_code": vip_client.client_code,
                    },
                    "appointment": {
                        "id": event.appointment_id,
                    },
                },
                reason="credits from referral in appointment",
                performed_at=datetime.now(timezone.utc),
            )

            uow.audit_logs.create(log)

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.exceptions.marketing import (
    CreditMustBePositiveError,
    ZeroCreditQuantityNotAllowedError,
)
from app.domain.utils.ensure_enum import ensure_enum
from app.domain.studio.finances.enums.client_credit_source_type import (
    ClientCreditSourceType,
)

"""
Represents a credit ledger entry for a VIP client.

Each entry records a change in the client's credit balance.
Entries are immutable, and the client's total credits are calculated
by summing the quantity of all entries.

Most properties are self-explanatory, but `source_id` requires clarification.

`source_id` is a polymorphic foreign key reference. Its meaning depends
on the value of `source_type`.

`source_type` acts as a discriminator that defines how `source_id`
should be interpreted.

- If `source_type` is related to an indication or appointment usage,
  `source_id` refers to the ID of a record in the appointments table.
- If `source_type` represents an admin action, `source_id` refers
  to the ID of a user (admin) in the users table.
"""


class ClientCreditEntry:
    def __init__(
        self,
        *,
        id: UUID | None = None,
        vip_client_id: UUID,
        source_id: UUID,
        source_type: ClientCreditSourceType,
        related_entry_id: UUID | None = None,
        quantity: int,
        reason: str = "",
        created_at: datetime | None = None,
    ):
        now = datetime.now(timezone.utc)

        if quantity == 0:
            raise ZeroCreditQuantityNotAllowedError(
                "Credit entry quantity cannot be zero"
            )

        self.id = id or uuid4()
        self.vip_client_id = vip_client_id
        self.source_id = source_id
        self.source_type = ensure_enum(source_type, ClientCreditSourceType)
        self.related_entry_id = related_entry_id
        self.quantity = quantity
        self.reason = reason
        self.created_at = created_at or now

    @classmethod
    def _create(
        cls,
        *,
        vip_client_id: UUID,
        source_id: UUID,
        source_type: ClientCreditSourceType,
        quantity: int,
        reason: str,
        related_entry_id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> "ClientCreditEntry":
        return cls(
            vip_client_id=vip_client_id,
            source_id=source_id,
            source_type=source_type,
            quantity=quantity,
            reason=reason,
            related_entry_id=related_entry_id,
            created_at=created_at,
        )

    @property
    def is_credit(self) -> bool:
        return self.quantity > 0

    @property
    def is_debit(self) -> bool:
        return self.quantity < 0

    @classmethod
    def create_indication(
        cls,
        *,
        vip_client_id: UUID,
        appointment_id: UUID,
        quantity: int,
        created_at: datetime | None = None,
    ) -> "ClientCreditEntry":

        if quantity <= 0:
            raise CreditMustBePositiveError("Indication credit must be positive")

        return cls._create(
            vip_client_id=vip_client_id,
            source_id=appointment_id,
            source_type=ClientCreditSourceType.INDICATION,
            quantity=quantity,
            reason="Créditos referentes a indicação.",
            created_at=created_at,
        )

    @classmethod
    def added_by_admin(
        cls,
        *,
        vip_client_id: UUID,
        admin_id: UUID,
        quantity: int,
        reason: str,
        created_at: datetime | None = None,
    ) -> "ClientCreditEntry":

        if quantity <= 0:
            raise CreditMustBePositiveError("Admin added credit must be positive")

        return cls._create(
            vip_client_id=vip_client_id,
            source_id=admin_id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=quantity,
            reason=reason,
            created_at=created_at,
        )

    @classmethod
    def used_in_appointment(
        cls,
        *,
        vip_client_id: UUID,
        appointment_id: UUID,
        quantity: int,
        created_at: datetime | None = None,
    ) -> "ClientCreditEntry":

        if quantity <= 0:
            raise CreditMustBePositiveError("Used credit must be positive")

        return cls._create(
            vip_client_id=vip_client_id,
            source_id=appointment_id,
            source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
            quantity=-abs(quantity),
            reason="Créditos usados em appointment",
            created_at=created_at,
        )

    @classmethod
    def reverse(
        cls,
        *,
        vip_client_id: UUID,
        admin_id: UUID,
        original_entry_id: UUID,
        quantity: int,
        reason: str,
        created_at: datetime | None = None,
    ) -> "ClientCreditEntry":

        if quantity <= 0:
            raise CreditMustBePositiveError("Reversal quantity must be positive")

        return cls._create(
            vip_client_id=vip_client_id,
            source_id=admin_id,
            source_type=ClientCreditSourceType.REVERSED_BY_ADMIN,
            quantity=-abs(quantity),
            reason=reason,
            related_entry_id=original_entry_id,
            created_at=created_at,
        )

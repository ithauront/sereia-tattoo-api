from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
from app.core.exceptions.appointments import (
    AppointmentMustBeInCorrectPreviousStatusError,
    AppointmentMustBeScheduledError,
    AppointmentMustHaveRealisticTimeAndDateError,
    AppointmentStatusBreakingDomainRules,
    AppointmentWasNotFullyPaidError,
    CurrentSessionMustBeLessThanTotalError,
    CurrentSessionMustBePositiveError,
    PriceMustBeDefinedError,
    PriceMustBePositiveError,
    TotalSessionsNumberMustBeDefineError,
    TotalSessionsNumberMustBePositiveError,
)
from app.domain.studio.appointments.enums.appointment_enums import (
    AppointmentStatus,
    AppointmentType,
)
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.value_objects.client_code import ClientCode


# TODO: fazer o repo, o fake repo e o teste do fake repo
class Appointment:
    def __init__(
        self,
        *,
        id: UUID | None = None,
        status: AppointmentStatus,
        appointment_type: AppointmentType,
        start_at: datetime,
        end_at: datetime,
        placement: str,
        details: str,
        size: str | None = None,
        current_session: int | None = None,
        total_sessions: int | None = None,
        color: bool = False,
        price: Decimal | None = None,
        deposit_confirmed_at: datetime | None = None,
        client_info: ClientInfo,
        referral_code: ClientCode | None = None,
        is_posted_on_socials: bool = False,
        observations: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        # TODO: pensar uma maneira de logar quem fez as modificações
        now = self._utc_now()

        self.id = id or uuid4()
        self.status = status
        self.appointment_type = appointment_type
        self.start_at = start_at
        self.end_at = end_at
        self.placement = placement
        self.details = details
        self.size = size
        self.current_session = current_session
        self.total_sessions = total_sessions
        self.color = color
        self.price = price
        self.deposit_confirmed_at = deposit_confirmed_at
        self.client_info = client_info
        self.referral_code = referral_code
        self.is_posted_on_socials = is_posted_on_socials
        self.observations = observations
        self.created_at = created_at or now
        self.updated_at = updated_at or now

        self._validate_state()

    @classmethod
    def create(
        cls,
        *,
        appointment_type: AppointmentType,
        start_at: datetime,
        end_at: datetime,
        placement: str,
        details: str,
        size: str | None = None,
        color: bool = False,
        client_info: ClientInfo,
        referral_code: ClientCode | None = None,
    ) -> "Appointment":
        if end_at <= start_at:
            raise AppointmentMustHaveRealisticTimeAndDateError()
        return cls(
            status=AppointmentStatus.REQUESTED,
            appointment_type=appointment_type,
            start_at=start_at,
            end_at=end_at,
            placement=placement,
            details=details,
            size=size,
            color=color,
            client_info=client_info,
            referral_code=referral_code,
        )

    def set_price(self, price: Decimal):
        # we usualy will use quote method. set_price method is only for changments in price
        if price <= 0:
            raise PriceMustBePositiveError()

        self.price = price
        self._touch()

    def set_sessions_total(self, total_sessions: int):
        if total_sessions < 1:
            raise TotalSessionsNumberMustBePositiveError()

        self.total_sessions = total_sessions

        if self.current_session is None:
            self.current_session = 1

        self._touch()

    def set_current_session(self, current_session: int):
        if not self.total_sessions:
            raise TotalSessionsNumberMustBeDefineError()
        if current_session < 1:
            raise CurrentSessionMustBePositiveError()
        if current_session > self.total_sessions:
            raise CurrentSessionMustBeLessThanTotalError()
            # if we raise this error we should tell user to change total_sessions
        self.current_session = current_session
        self._touch()

    def update_color(self, color: bool):
        self.color = color
        self._touch()

    def mark_as_posted_on_socials(self):
        self.is_posted_on_socials = True
        self._touch()

    def quote(self, price: Decimal):
        if self.status != AppointmentStatus.REQUESTED:
            raise AppointmentMustBeInCorrectPreviousStatusError()
        if price <= 0:
            raise PriceMustBePositiveError()

        self.price = price
        self.status = AppointmentStatus.QUOTED
        self._touch()

    def confirm_deposit(self):
        if self.status != AppointmentStatus.QUOTED:
            raise AppointmentMustBeInCorrectPreviousStatusError()
        if self.price is None:
            raise PriceMustBeDefinedError()

        self.deposit_confirmed_at = self._utc_now()
        self.status = AppointmentStatus.SCHEDULED
        self._touch()

    def complete(self, total_paid: Decimal):
        if self.price is None:
            raise PriceMustBeDefinedError()

        if self.status != AppointmentStatus.SCHEDULED:
            raise AppointmentMustBeScheduledError()

        if total_paid < self.price:
            raise AppointmentWasNotFullyPaidError()

        self.status = AppointmentStatus.COMPLETED
        self._touch()

    def mark_as_canceled(self, observations: str):
        self.status = AppointmentStatus.CANCELED
        self.add_observations(observations)

    def add_observations(self, new_observation: str):
        if self.observations:
            self.observations += f"\n{new_observation}"
        else:
            self.observations = new_observation
        self._touch()

    def _touch(self):
        self.updated_at = self._utc_now()

    def _validate_state(self):
        if self.status == AppointmentStatus.REQUESTED:
            if self.price is not None:
                raise AppointmentStatusBreakingDomainRules(
                    "status_requested_does_not_suport_price"
                )
            if self.deposit_confirmed_at is not None:
                raise AppointmentStatusBreakingDomainRules(
                    "status_requested_does_not_suport_deposit"
                )

        elif self.status == AppointmentStatus.QUOTED:
            if self.price is None:
                raise AppointmentStatusBreakingDomainRules(
                    "status_quoted_must_have_price"
                )
            if self.deposit_confirmed_at is not None:
                raise AppointmentStatusBreakingDomainRules(
                    "status_quoted_does_not_suport_deposit"
                )

        elif self.status == AppointmentStatus.SCHEDULED:
            if self.price is None:
                raise AppointmentStatusBreakingDomainRules(
                    "status_scheduled_must_have_price"
                )
            if self.deposit_confirmed_at is None:
                raise AppointmentStatusBreakingDomainRules(
                    "status_scheduled_must_have_deposit"
                )

        if self.end_at <= self.start_at:
            raise AppointmentMustHaveRealisticTimeAndDateError()

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

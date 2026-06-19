# TODO: completar fazendo os metodos e tudo mais
# TODO: fazer repo
# TODO: fazer sql model and repo
# TODO: fazer fake repo e teste do repo real e fake
from datetime import datetime, time, timezone
from uuid import UUID, uuid4

from app.core.exceptions.calendar import WorkingPeriodMustHaveRealisticTimeAndDateError


class WorkingPeriod:
    def __init__(
        self,
        *,
        id: UUID | None = None,
        provider_id: UUID,
        start_at: time,
        end_at: time,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        now = self._utc_now()

        self.id = id or uuid4()
        self.provider_id = provider_id
        self.start_at = start_at
        self.end_at = end_at
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    @classmethod
    def create(
        cls,
        *,
        provider_id: UUID,
        start_at: time,
        end_at: time,
    ) -> "WorkingPeriod":
        if end_at <= start_at:
            raise WorkingPeriodMustHaveRealisticTimeAndDateError()
        return cls(provider_id=provider_id, start_at=start_at, end_at=end_at)

    def update_period(self, *, start_at: time, end_at: time):
        if end_at <= start_at:
            raise WorkingPeriodMustHaveRealisticTimeAndDateError()
        self.start_at = start_at
        self.end_at = end_at
        self._touch()

    def is_available_for(self, *, start: time, end: time) -> bool:
        """
        Check if a time range fits inside this working period.
        Return if user is available for the time range
        """
        return self.start_at <= start and end <= self.end_at

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    def _touch(self):
        self.updated_at = datetime.now(timezone.utc)

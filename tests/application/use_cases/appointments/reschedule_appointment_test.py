from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.application.studio.use_cases.appointments_use_cases import reschedule_appointment_use_case
from app.application.studio.use_cases.appointments_use_cases.reschedule_appointment_use_case import (
    RescheduleAppointmentUseCase,
)
from app.application.studio.use_cases.DTO.reschedule_appointment_dto import RescheduleAppointmentInput
from app.core.exceptions.appointments import (
    AppointmentMustHaveRealisticTimeAndDateError,
    AppointmentNotFoundError,
    ConfirmedDepositWithoutActivePaymentError,
    IncorrectAppointmentStatusError,
    OnlyAdminOrOwnerOfAppointmentError,
    ReasonForDepositRetentionOverrideMustBeProvidedError,
    SlotIsAlreadyOccupiedError,
)
from app.core.exceptions.calendar import (
    CannotFindWorkingPeriodsForThisUserError,
    UserIsNotWorkingInDesignatedTimeframeError,
)
from app.core.exceptions.validation import ValidationError
from app.core.types.appointment_enums import AppointmentStatus
from app.core.types.calendar_enums import CalendarExceptionType
from app.core.types.payment_enums import PaymentAllocationStatus, PaymentPurposeType
from app.domain.studio.appointments.policies.appointment_authorization_policy import (
    AppointmentAuthorizationPolicy,
)
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)
from app.domain.studio.appointments.policies.deposit_policy import DepositPolicy
from tests.fakes.fake_event_bus import FakeIntegrationEventBus

NOW = datetime(2035, 1, 1, 9, tzinfo=timezone.utc)


@pytest.fixture
def scenario(
    monkeypatch,
    write_uow,
    read_uow,
    make_user,
    make_scheduled_appointment,
    make_calendar_settings,
    make_payment,
):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW.astimezone(tz) if tz else NOW.replace(tzinfo=None)

    monkeypatch.setattr(reschedule_appointment_use_case, "datetime", Clock)

    def build(*, role="owner", advance=timedelta(hours=24)):
        owner = make_user()
        actor = owner if role == "owner" else make_user(is_admin=role == "admin")
        write_uow.users.create(owner)
        if actor.id != owner.id:
            write_uow.users.create(actor)
        appointment = make_scheduled_appointment(
            user_id=owner.id,
            start_at=NOW + advance,
            end_at=NOW + advance + timedelta(hours=1),
            project_id=uuid4(),
            current_session=1,
            total_sessions=3,
        )
        write_uow.appointments.create(appointment)
        write_uow.calendar_settings.create(make_calendar_settings(user_id=owner.id))
        deposit = make_payment(
            appointment_id=appointment.id,
            payment_purpose=PaymentPurposeType.DEPOSIT,
        )
        write_uow.payments.create(deposit)
        bus = FakeIntegrationEventBus()
        use_case = RescheduleAppointmentUseCase(
            write_uow=write_uow,
            read_uow=read_uow,
            calendar_policy=CalendarAvailabilityPolicy(),
            deposit_policy=DepositPolicy(),
            authorization_policy=AppointmentAuthorizationPolicy(),
            integration_bus=bus,
        )
        data = RescheduleAppointmentInput(
            appointment_id=appointment.id,
            actor=actor,
            start_at=NOW + timedelta(days=7),
            end_at=NOW + timedelta(days=7, hours=1),
        )
        return SimpleNamespace(
            appointment=appointment,
            deposit=deposit,
            use_case=use_case,
            data=data,
            bus=bus,
            uow=write_uow,
        )

    return build


def audit(s):
    logs = s.uow.audit_logs.find_many_by_entity_id(s.appointment.id)
    assert len(logs) == 1
    return logs[0]


async def test_partial_allow_rejection_does_not_retain_deposit_or_publish_event(
    scenario,
    make_calendar_exception,
):
    # Expediente 08h–12h, ALLOW 14h–16h, pedido 15h–17h: falta cobrir 16h–17h.
    s = scenario()
    data = replace(
        s.data,
        start_at=s.data.start_at.replace(hour=15),
        end_at=s.data.end_at.replace(hour=17),
    )
    s.uow.calendar_exceptions.create(
        make_calendar_exception(
            calendar_of_user=s.appointment.user_id,
            start_at=data.start_at.replace(hour=14),
            end_at=data.end_at.replace(hour=16),
            exception_type=CalendarExceptionType.ALLOW,
        )
    )
    original_appointment = vars(s.appointment).copy()
    original_payment = vars(s.deposit).copy()

    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        await s.use_case.execute(data)

    assert vars(s.appointment) == original_appointment
    assert vars(s.deposit) == original_payment
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.bus.events == []
    assert not s.uow.committed


@pytest.mark.parametrize("missing", ["appointment", "calendar"])
async def test_missing_resources_reject_without_changes(scenario, monkeypatch, missing):
    s = scenario()
    data = s.data
    if missing == "appointment":
        data = replace(data, appointment_id=uuid4())
        error = AppointmentNotFoundError
    else:
        monkeypatch.setattr(s.uow.calendar_settings, "find_by_user_id", lambda _: None)
        error = CannotFindWorkingPeriodsForThisUserError
    before = vars(s.appointment).copy()
    with pytest.raises(error):
        await s.use_case.execute(data)
    assert vars(s.appointment) == before
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.bus.events == []
    assert not s.uow.committed


@pytest.mark.parametrize("role", ["owner", "admin"])
@pytest.mark.parametrize("blocked", [False, True])
async def test_booking_window_bypass_does_not_bypass_calendar(
    scenario,
    make_calendar_exception,
    role,
    blocked,
):
    s = scenario(role=role)
    calendar = s.uow.calendar_settings.find_by_user_id(s.appointment.user_id)
    calendar.booking_window_until = NOW.date()
    if blocked:
        s.uow.calendar_exceptions.create(
            make_calendar_exception(
                calendar_of_user=s.appointment.user_id,
                start_at=s.data.start_at,
                end_at=s.data.end_at,
                exception_type=CalendarExceptionType.BLOCK,
            )
        )
        data = s.data
    else:
        data = replace(
            s.data,
            start_at=s.data.start_at.replace(hour=23),
            end_at=s.data.end_at.replace(hour=23, minute=30),
        )
    before = vars(s.appointment).copy()
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        await s.use_case.execute(
            replace(
                data,
                override_deposit_retention=True,
                deposit_override_reason="Pedido do cliente",
            )
        )
    assert vars(s.appointment) == before
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.bus.events == []
    assert not s.uow.committed


@pytest.mark.parametrize("role", ["owner", "admin"])
async def test_authorized_actor_can_reschedule_beyond_booking_window(scenario, role):
    s = scenario(role=role)
    calendar = s.uow.calendar_settings.find_by_user_id(s.appointment.user_id)
    calendar.booking_window_until = NOW.date()
    result = await s.use_case.execute(s.data)
    assert result.start_at == s.data.start_at
    assert s.uow.committed
    assert len(s.bus.events) == 1


async def test_full_allow_exception_permits_reschedule_outside_working_hours(
    scenario,
    make_calendar_exception,
):
    s = scenario()
    data = replace(
        s.data,
        start_at=s.data.start_at.replace(hour=23),
        end_at=s.data.end_at.replace(hour=23, minute=30),
    )
    s.uow.calendar_exceptions.create(
        make_calendar_exception(
            calendar_of_user=s.appointment.user_id,
            start_at=data.start_at,
            end_at=data.end_at,
            exception_type=CalendarExceptionType.ALLOW,
        )
    )
    result = await s.use_case.execute(data)
    assert result.start_at == data.start_at
    assert result.end_at == data.end_at
    assert s.uow.committed
    assert len(s.bus.events) == 1


@pytest.mark.parametrize("role", ["owner", "admin"])
@pytest.mark.parametrize("override", [False, True])
async def test_past_no_show_can_be_rescheduled_preserving_identity(scenario, role, override):
    s = scenario(role=role, advance=timedelta(days=-7))
    identity = (
        s.appointment.id,
        s.appointment.project_id,
        s.appointment.current_session,
        s.appointment.total_sessions,
    )
    old_start = s.appointment.start_at
    result = await s.use_case.execute(
        replace(
            s.data,
            override_deposit_retention=override,
            deposit_override_reason="Exceção autorizada pelo estúdio" if override else None,
        )
    )
    assert (
        s.appointment.id,
        s.appointment.project_id,
        s.appointment.current_session,
        s.appointment.total_sessions,
    ) == identity
    assert result.start_at == s.data.start_at
    assert result.status == (AppointmentStatus.SCHEDULED if override else AppointmentStatus.QUOTED)
    assert result.was_deposit_retained is (not override)
    assert result.deposit_override_applied is override
    assert (s.appointment.deposit_confirmed_at is not None) is override
    assert s.deposit.allocation_status == (
        PaymentAllocationStatus.ACTIVE if override else PaymentAllocationStatus.RETAINED
    )
    assert audit(s).changes["old_start_at"] == old_start.isoformat()
    assert len(s.bus.events) == 1
    assert s.bus.events[0].was_deposit_retained is (not override)


@pytest.mark.parametrize("status", [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELED])
async def test_past_terminal_appointment_cannot_be_rescheduled(scenario, status):
    s = scenario(advance=timedelta(days=-7))
    s.appointment.status = status
    old_start = s.appointment.start_at
    with pytest.raises(IncorrectAppointmentStatusError):
        await s.use_case.execute(s.data)
    assert s.appointment.start_at == old_start
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    assert not s.uow.committed
    assert s.bus.events == []
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []


@pytest.mark.parametrize("advance", [timedelta(days=-7), timedelta(days=3)])
@pytest.mark.parametrize("override", [False, True])
@pytest.mark.parametrize("payments_kind", ["empty", "retained", "other_purpose"])
async def test_inconsistent_confirmed_deposit_is_rejected_without_changes(
    scenario,
    monkeypatch,
    advance,
    override,
    payments_kind,
):
    s = scenario(advance=advance)
    if payments_kind == "empty":
        monkeypatch.setattr(s.uow.payments, "find_many_by_appointment_id", lambda _: [])
    elif payments_kind == "retained":
        s.deposit.retain_deposit(reason="Retenção anterior", retained_at=NOW - timedelta(days=10))
    else:
        s.deposit.payment_purpose = PaymentPurposeType.APPOINTMENT
    before_appointment = vars(s.appointment).copy()
    before_payment = vars(s.deposit).copy()
    with pytest.raises(ConfirmedDepositWithoutActivePaymentError):
        await s.use_case.execute(
            replace(
                s.data,
                override_deposit_retention=override,
                deposit_override_reason="Exceção autorizada pelo estúdio" if override else None,
            )
        )
    assert vars(s.appointment) == before_appointment
    assert vars(s.deposit) == before_payment
    assert not s.uow.committed
    assert s.bus.events == []
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []


@pytest.mark.parametrize("status", [AppointmentStatus.REQUESTED, AppointmentStatus.QUOTED])
async def test_unconfirmed_appointment_keeps_status_on_reschedule(scenario, status):
    s = scenario()
    s.appointment.status = status
    s.appointment.deposit_confirmed_at = None
    result = await s.use_case.execute(s.data)
    assert result.status == status
    assert not result.was_deposit_retained
    assert not result.deposit_override_applied
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE


@pytest.mark.parametrize("role", ["owner", "admin"])
async def test_authorized_override_preserves_deposit_and_records_reason(scenario, role):
    s = scenario(role=role)
    original_confirmation = s.appointment.deposit_confirmed_at
    project = (s.appointment.project_id, s.appointment.current_session, s.appointment.total_sessions)
    await s.use_case.execute(
        replace(
            s.data,
            override_deposit_retention=True,
            deposit_override_reason="  Alteração do estúdio  ",
        )
    )
    assert s.appointment.status == AppointmentStatus.SCHEDULED
    assert s.appointment.deposit_confirmed_at == original_confirmation
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    assert s.appointment.start_at == s.data.start_at
    assert (
        s.appointment.project_id,
        s.appointment.current_session,
        s.appointment.total_sessions,
    ) == project
    log = audit(s)
    assert log.actor_id == s.data.actor.id
    assert log.changes["deposit_retention_override_requested"] is True
    assert log.changes["deposit_retention_override_applied"] is True
    assert log.changes["deposit_retention_override_reason"] == "Alteração do estúdio"
    assert log.changes["retained_payment_ids"] == []
    assert s.uow.committed


@pytest.mark.parametrize("reason", [None, "", " \t\n "])
async def test_override_requires_nonblank_reason_before_mutating(scenario, reason):
    s = scenario()
    original = (s.appointment.start_at, s.appointment.end_at, s.appointment.deposit_confirmed_at)
    with pytest.raises(ReasonForDepositRetentionOverrideMustBeProvidedError):
        await s.use_case.execute(
            replace(s.data, override_deposit_retention=True, deposit_override_reason=reason)
        )
    assert (s.appointment.start_at, s.appointment.end_at, s.appointment.deposit_confirmed_at) == original
    assert s.appointment.status == AppointmentStatus.SCHEDULED
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.bus.events == []
    assert not s.uow.committed


@pytest.mark.parametrize(
    ("reason", "message"),
    [
        ("a", "text_must_have_at_least_5_characters"),
        ("  abcd  ", "text_must_have_at_least_5_characters"),
        ("12345", "text_must_contain_letters"),
        ("!!!!!", "text_must_contain_letters"),
    ],
)
async def test_override_rejects_invalid_text_before_mutating(scenario, reason, message):
    s = scenario()
    original = (s.appointment.start_at, s.appointment.end_at, s.appointment.deposit_confirmed_at)
    with pytest.raises(ValidationError, match=message):
        await s.use_case.execute(
            replace(s.data, override_deposit_retention=True, deposit_override_reason=reason)
        )
    assert (s.appointment.start_at, s.appointment.end_at, s.appointment.deposit_confirmed_at) == original
    assert s.appointment.status == AppointmentStatus.SCHEDULED
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.bus.events == []
    assert not s.uow.committed


async def test_override_accepts_minimum_length_and_normalizes_reason(scenario):
    s = scenario()
    await s.use_case.execute(
        replace(s.data, override_deposit_retention=True, deposit_override_reason="  Falha  ")
    )
    assert audit(s).changes["deposit_retention_override_reason"] == "Falha"
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE


@pytest.mark.parametrize("override", [False, True])
async def test_unrelated_artist_cannot_reschedule_even_with_override(scenario, override):
    s = scenario(role="other")
    old_start = s.appointment.start_at
    with pytest.raises(OnlyAdminOrOwnerOfAppointmentError):
        await s.use_case.execute(
            replace(
                s.data,
                override_deposit_retention=override,
                deposit_override_reason="Pedido do cliente",
            )
        )
    assert s.appointment.start_at == old_start
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.bus.events == []


@pytest.mark.parametrize("role", ["owner", "admin"])
async def test_without_override_retains_only_active_deposits(scenario, make_payment, role):
    s = scenario(role=role)
    old_start, old_end = s.appointment.start_at, s.appointment.end_at
    old_deposit = make_payment(
        appointment_id=s.appointment.id,
        payment_purpose=PaymentPurposeType.DEPOSIT,
    )
    old_deposit.retain_deposit(reason="Retenção anterior", retained_at=NOW - timedelta(days=5))
    payment = make_payment(
        appointment_id=s.appointment.id, payment_purpose=PaymentPurposeType.APPOINTMENT
    )
    s.uow.payments.create(old_deposit)
    s.uow.payments.create(payment)
    await s.use_case.execute(replace(s.data, deposit_override_reason="Não foi solicitada exceção"))
    assert s.appointment.status == AppointmentStatus.QUOTED
    assert s.appointment.deposit_confirmed_at is None
    assert s.deposit.allocation_status == PaymentAllocationStatus.RETAINED
    assert s.deposit.payment_purpose == PaymentPurposeType.DEPOSIT
    assert old_deposit.allocation_change_reason == "Retenção anterior"
    assert payment.allocation_status == PaymentAllocationStatus.ACTIVE
    changes = audit(s).changes
    assert changes["old_start_at"] == old_start.isoformat()
    assert changes["old_end_at"] == old_end.isoformat()
    assert changes["old_status"] == AppointmentStatus.SCHEDULED.value
    assert changes["new_status"] == AppointmentStatus.QUOTED.value
    assert changes["retained_payment_ids"] == [str(s.deposit.id)]
    assert changes["was_deposit_retained"] is True
    assert changes["deposit_retention_override_reason"] is None
    assert changes["deposit_retention_override_applied"] is False


@pytest.mark.parametrize("override", [False, True])
async def test_within_notice_period_keeps_deposit_without_applying_override(scenario, override):
    s = scenario(advance=timedelta(hours=48))
    await s.use_case.execute(
        replace(
            s.data,
            override_deposit_retention=override,
            deposit_override_reason="Solicitado pelo operador" if override else None,
        )
    )
    assert s.appointment.status == AppointmentStatus.SCHEDULED
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    changes = audit(s).changes
    assert changes["deposit_retention_override_requested"] is override
    assert changes["deposit_retention_override_applied"] is False
    assert changes["was_deposit_retained"] is False


async def test_same_interval_does_not_retain_or_audit(scenario):
    s = scenario()
    await s.use_case.execute(
        replace(s.data, start_at=s.appointment.start_at, end_at=s.appointment.end_at)
    )
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    assert s.appointment.status == AppointmentStatus.SCHEDULED
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.bus.events == []


async def test_invalid_interval_does_not_retain_deposit(scenario):
    s = scenario()
    old_start = s.appointment.start_at
    with pytest.raises(AppointmentMustHaveRealisticTimeAndDateError):
        await s.use_case.execute(replace(s.data, end_at=s.data.start_at))
    assert s.appointment.start_at == old_start
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    assert s.appointment.status == AppointmentStatus.SCHEDULED
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.bus.events == []


async def test_override_does_not_bypass_calendar_conflict(scenario, make_scheduled_appointment):
    s = scenario()
    other = make_scheduled_appointment(
        user_id=s.appointment.user_id,
        start_at=s.data.start_at,
        end_at=s.data.end_at,
    )
    s.uow.appointments.create(other)
    with pytest.raises(SlotIsAlreadyOccupiedError):
        await s.use_case.execute(
            replace(
                s.data,
                override_deposit_retention=True,
                deposit_override_reason="Pedido do cliente",
            )
        )
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.bus.events == []


@pytest.mark.parametrize("override", [False, True])
async def test_returns_final_state_after_commit(scenario, override):
    s = scenario()
    result = await s.use_case.execute(
        replace(
            s.data,
            override_deposit_retention=override,
            deposit_override_reason="Pedido do cliente",
        )
    )
    assert result.appointment_id == s.appointment.id
    assert result.start_at == s.data.start_at
    assert result.end_at == s.data.end_at
    assert result.status == (AppointmentStatus.SCHEDULED if override else AppointmentStatus.QUOTED)
    assert result.was_deposit_retained is (not override)
    assert result.deposit_override_applied is override
    assert result.start_at.tzinfo is timezone.utc
    assert s.uow.committed


async def test_equivalent_offset_interval_returns_state_without_changes(scenario):
    s = scenario()
    offset = timezone(timedelta(hours=-3))
    result = await s.use_case.execute(
        replace(
            s.data,
            start_at=s.appointment.start_at.astimezone(offset),
            end_at=s.appointment.end_at.astimezone(offset),
            override_deposit_retention=True,
            deposit_override_reason="Pedido do cliente",
        )
    )
    assert result.start_at == s.appointment.start_at
    assert result.status == AppointmentStatus.SCHEDULED
    assert result.was_deposit_retained is False
    assert result.deposit_override_applied is False
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.bus.events == []
    assert s.uow.committed


@pytest.mark.parametrize("field", ["start_at", "end_at"])
@pytest.mark.parametrize("output", [False, True])
async def test_dtos_reject_naive_datetimes(scenario, field, output):
    from app.application.studio.use_cases.DTO.reschedule_appointment_dto import (
        RescheduleAppointmentOutput,
    )

    s = scenario()
    dto = s.data
    if output:
        dto = RescheduleAppointmentOutput(
            appointment_id=s.appointment.id,
            start_at=s.data.start_at,
            end_at=s.data.end_at,
            status=s.appointment.status,
            was_deposit_retained=False,
            deposit_override_applied=False,
        )
    with pytest.raises(AppointmentMustHaveRealisticTimeAndDateError):
        replace(dto, **{field: getattr(dto, field).replace(tzinfo=None)})


async def test_offset_input_is_normalized_before_calendar_validation(scenario):
    s = scenario()
    offset = timezone(timedelta(hours=9))
    data = replace(
        s.data, start_at=s.data.start_at.astimezone(offset), end_at=s.data.end_at.astimezone(offset)
    )
    assert data.start_at.tzinfo is timezone.utc
    # 18:00+09:00 is 09:00 UTC, inside the 08:00-12:00 working period.
    result = await s.use_case.execute(data)
    assert result.start_at == s.data.start_at
    assert result.end_at.tzinfo is timezone.utc
    assert audit(s).performed_at == NOW
    assert s.deposit.allocation_changed_at == NOW


@pytest.mark.parametrize("advance", [timedelta(0), timedelta(days=-1)])
async def test_past_or_present_noop_is_rejected(scenario, advance):
    s = scenario(advance=advance)
    with pytest.raises(AppointmentMustHaveRealisticTimeAndDateError):
        await s.use_case.execute(
            replace(s.data, start_at=s.appointment.start_at, end_at=s.appointment.end_at)
        )
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.bus.events == []


async def test_commit_failure_does_not_return_success(scenario, monkeypatch):
    s = scenario()

    def fail_commit():
        raise RuntimeError("commit failed")

    monkeypatch.setattr(s.uow, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="commit failed"):
        await s.use_case.execute(s.data)
    assert s.bus.events == []


@pytest.mark.parametrize("override", [False, True])
async def test_event_is_published_once_after_commit_with_final_deposit_decision(
    scenario, monkeypatch, override
):
    s = scenario()
    original_publish = s.bus.publish

    async def publish_after_commit(event, **context):
        assert s.uow.committed
        await original_publish(event, **context)

    monkeypatch.setattr(s.bus, "publish", publish_after_commit)
    result = await s.use_case.execute(
        replace(
            s.data,
            override_deposit_retention=override,
            deposit_override_reason="Pedido do cliente",
        )
    )
    assert len(s.bus.events) == 1
    event = s.bus.events[0]
    assert event.start_at == result.start_at
    assert event.end_at == result.end_at
    assert event.user_id == s.appointment.user_id
    assert event.client_email_or_vip_id == s.appointment.client_info.email
    assert event.appointment_type == s.appointment.appointment_type
    assert event.was_deposit_retained == result.was_deposit_retained == (not override)


async def test_ordinary_reschedule_publishes_without_retention(scenario):
    s = scenario(advance=timedelta(days=3))
    await s.use_case.execute(s.data)
    assert len(s.bus.events) == 1
    assert s.bus.events[0].was_deposit_retained is False


async def test_noop_commit_failure_does_not_publish(scenario, monkeypatch):
    s = scenario()

    def fail_commit():
        raise RuntimeError("commit failed")

    monkeypatch.setattr(s.uow, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="commit failed"):
        await s.use_case.execute(
            replace(
                s.data,
                start_at=s.appointment.start_at,
                end_at=s.appointment.end_at,
            )
        )
    assert s.bus.events == []

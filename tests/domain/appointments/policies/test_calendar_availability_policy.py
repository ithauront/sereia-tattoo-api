from datetime import datetime, timedelta, timezone

import pytest

from app.core.exceptions.appointments import SlotIsNotAvailableError
from app.core.exceptions.calendar import UserIsNotWorkingInDesignatedTimeframeError
from app.core.types.calendar_enums import CalendarExceptionType
from app.domain.studio.appointments.entities.calendar_settings import CalendarSettings
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)

DAY = datetime(2035, 1, 8, tzinfo=timezone.utc)


def at(hour):
    return DAY.replace(hour=hour)


@pytest.fixture
def calendar(make_calendar_settings, monkeypatch):
    monkeypatch.setattr(CalendarSettings, "_utc_now", staticmethod(lambda: DAY - timedelta(days=1)))
    return make_calendar_settings(booking_window_until=(DAY + timedelta(days=30)).date())


@pytest.fixture
def allow(calendar, make_calendar_exception):
    def build(start, end):
        return make_calendar_exception(
            calendar_of_user=calendar.user_id,
            start_at=at(start),
            end_at=at(end),
            exception_type=CalendarExceptionType.ALLOW,
        )

    return build


@pytest.fixture
def block(calendar, make_calendar_exception):
    def build(start, end):
        return make_calendar_exception(
            calendar_of_user=calendar.user_id,
            start_at=at(start),
            end_at=at(end),
            exception_type=CalendarExceptionType.BLOCK,
        )

    return build


def check(calendar, start, end, *exceptions, ignore_booking_window=False):
    return CalendarAvailabilityPolicy().can_schedule(
        calendar_settings=calendar,
        calendar_exceptions=list(exceptions),
        start_at=at(start),
        end_at=at(end),
        can_ignore_booking_window=ignore_booking_window,
    )


def test_working_hours_without_exceptions_are_available(calendar):
    """09h–10h está no expediente 08h–12h."""
    assert check(calendar, 9, 10) is None


def test_outside_working_hours_without_exceptions_is_rejected(calendar):
    """15h–16h não tem expediente nem ALLOW."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 15, 16)


def test_full_allow_permits_time_outside_working_hours(calendar, allow):
    """ALLOW 14h–16h cobre o pedido 15h–16h."""
    assert check(calendar, 15, 16, allow(14, 16)) is None


def test_partial_allow_does_not_release_uncovered_end(calendar, allow):
    """ALLOW 14h–16h não libera o trecho 16h–17h."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 15, 17, allow(14, 16))


def test_partial_allow_does_not_release_uncovered_start(calendar, allow):
    """ALLOW 14h–16h não libera o trecho 13h–14h."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 13, 15, allow(14, 16))


def test_allow_in_middle_does_not_release_both_uncovered_ends(calendar, allow):
    """ALLOW 14h–16h não libera 13h–14h nem 16h–17h."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 13, 17, allow(14, 16))


def test_working_hours_and_adjacent_allow_cover_whole_appointment(calendar, allow):
    """11h–12h usa expediente; 12h–14h usa ALLOW."""
    assert check(calendar, 11, 14, allow(12, 14)) is None


def test_allow_before_working_hours_joins_regular_availability(calendar, allow):
    """07h–08h usa ALLOW; 08h–09h usa expediente."""
    assert check(calendar, 7, 9, allow(7, 8)) is None


def test_gap_between_working_hours_and_allow_is_rejected(calendar, allow):
    """Expediente até 12h e ALLOW a partir de 14h deixam uma lacuna."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 11, 15, allow(14, 16))


def test_block_inside_working_hours_rejects_appointment(calendar, block):
    """BLOCK 09h–10h impede um horário dentro do expediente."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 9, 10, block(9, 10))


def test_shorter_block_inside_allow_wins_outside_working_hours(calendar, allow, block):
    """Dentro de ALLOW 14h–18h, BLOCK 15h–16h é mais curto e vence."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 15, 16, allow(14, 18), block(15, 16))


def test_block_in_middle_rejects_even_when_last_segment_is_allowed(calendar, allow, block):
    """Pedido 14h–18h tem ALLOW, BLOCK 15h–16h e ALLOW: basta um trecho bloqueado."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 14, 18, allow(14, 18), block(15, 16))


def test_shorter_allow_inside_block_opens_its_interval(calendar, allow, block):
    """Dentro de BLOCK 14h–18h, ALLOW 15h–16h é mais curto e vence."""
    assert check(calendar, 15, 16, block(14, 18), allow(15, 16)) is None


def test_shorter_allow_does_not_remove_surrounding_block(calendar, allow, block):
    """ALLOW 15h–16h não remove o BLOCK que continua em 16h–17h."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 15, 17, block(14, 18), allow(15, 16))


def test_block_wins_when_allow_and_block_have_same_duration(calendar, allow, block):
    """ALLOW e BLOCK 14h–16h: em empate vence BLOCK."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 14, 16, allow(14, 16), block(14, 16))


def test_block_wins_tie_regardless_of_list_order(calendar, allow, block):
    """Inverter a ordem da lista não muda a prioridade de BLOCK."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 14, 16, block(14, 16), allow(14, 16))


def test_equal_duration_shifted_exceptions_block_their_overlap(calendar, allow, block):
    """ALLOW 14h–16h e BLOCK 15h–17h duram 2h: BLOCK vence em 15h–16h."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 14, 16, allow(14, 16), block(15, 17))


def test_precedence_uses_original_duration_not_clipped_duration(calendar, allow, block):
    """Ambos cobrem o pedido inteiro, mas ALLOW dura 2h e BLOCK dura 6h."""
    assert check(calendar, 15, 16, allow(14, 16), block(13, 19)) is None


def test_separate_allow_cannot_hide_earlier_block(calendar, allow, block):
    """O ALLOW do último trecho não pode esconder o BLOCK do primeiro."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 14, 16, block(14, 15), allow(15, 16))


def test_adjacent_allows_cover_whole_interval(calendar, allow):
    """ALLOW 14h–15h e ALLOW 15h–16h não deixam lacuna, mesmo fora de ordem."""
    assert check(calendar, 14, 16, allow(15, 16), allow(14, 15)) is None


def test_overlapping_allows_cover_whole_interval(calendar, allow):
    """ALLOW 14h–16h e ALLOW 15h–17h cobrem todo o pedido."""
    assert check(calendar, 14, 17, allow(14, 16), allow(15, 17)) is None


def test_gap_between_allows_is_rejected(calendar, allow):
    """Entre ALLOW 14h–15h e ALLOW 16h–17h, falta cobrir 15h–16h."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 14, 17, allow(14, 15), allow(16, 17))


def test_allow_ending_at_appointment_start_does_not_apply(calendar, allow):
    """ALLOW até 15h não libera um pedido que começa às 15h."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 15, 16, allow(14, 15))


def test_allow_starting_at_appointment_end_does_not_apply(calendar, allow):
    """ALLOW a partir de 16h não libera um pedido que termina às 16h."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 15, 16, allow(16, 17))


def test_blocks_touching_boundaries_do_not_overlap(calendar, block):
    """BLOCK até 09h e BLOCK a partir de 10h não impedem 09h–10h."""
    assert check(calendar, 9, 10, block(8, 9), block(10, 11)) is None


def test_distant_exceptions_do_not_change_working_hours(calendar, allow, block):
    """Exceções da tarde não influenciam o expediente da manhã."""
    assert check(calendar, 9, 10, allow(14, 16), block(18, 19)) is None


def test_ignoring_booking_window_does_not_ignore_working_hours(calendar):
    """A permissão sobre a janela não libera a tarde sem ALLOW.
    Booking window é sobre o dia do agendamento e não sobre a hora"""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 15, 16, ignore_booking_window=True)


def test_ignoring_booking_window_does_not_ignore_block(calendar, block):
    """Mesmo autorizado, o operador não ultrapassa BLOCK."""
    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        check(calendar, 9, 10, block(9, 10), ignore_booking_window=True)


def test_outside_booking_window_requires_permission(calendar):
    """Expediente disponível, mas a janela fechou ontem."""
    calendar.booking_window_until = (DAY - timedelta(days=1)).date()
    with pytest.raises(SlotIsNotAvailableError):
        check(calendar, 9, 10)


def test_authorized_actor_can_ignore_booking_window(calendar):
    """Ignorar a janela permite o horário dentro do expediente."""
    calendar.booking_window_until = (DAY - timedelta(days=1)).date()
    assert check(calendar, 9, 10, ignore_booking_window=True) is None


def test_full_allow_can_override_booking_window(calendar, allow):
    """Mantém a regra atual: ALLOW completo também dispensa a janela."""
    calendar.booking_window_until = (DAY - timedelta(days=1)).date()
    assert check(calendar, 15, 16, allow(14, 16)) is None


def test_partial_allow_does_not_override_window_for_remaining_segment(calendar, allow):
    """ALLOW cobre 09h–10h; 10h–11h ainda depende da janela."""
    calendar.booking_window_until = (DAY - timedelta(days=1)).date()
    with pytest.raises(SlotIsNotAvailableError):
        check(calendar, 9, 11, allow(9, 10))

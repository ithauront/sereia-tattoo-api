from datetime import timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.events import get_integration_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.core.exceptions.appointments import (
    AppointmentClientContactInfoCorruptedError,
    AppointmentMustBeInCorrectPreviousStatusError,
    SlotIsNotAvailableError,
)
from app.core.types.appointment_enums import AppointmentStatus
from app.core.types.calendar_enums import CalendarExceptionType
from app.core.types.payment_enums import PaymentAllocationStatus
from app.main import app
from tests.application.use_cases.appointments import reschedule_appointment_test

scenario = reschedule_appointment_test.scenario
NOW = reschedule_appointment_test.NOW


@pytest.fixture
def route_scenario(scenario, read_uow, make_token):
    previous_overrides = app.dependency_overrides.copy()

    def build(**kwargs):
        s = scenario(**kwargs)
        app.dependency_overrides[get_write_unit_of_work] = lambda: s.uow
        app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow
        app.dependency_overrides[get_integration_event_bus] = lambda: s.bus
        return SimpleNamespace(
            state=s,
            url=f"/appointments/{s.appointment.id}/reschedule",
            headers={"Authorization": f"Bearer {make_token(s.data.actor)}"},
            body={
                "new_start_at": s.data.start_at.isoformat(),
                "new_end_at": s.data.end_at.isoformat(),
            },
        )

    yield build
    app.dependency_overrides = previous_overrides


def assert_rejected(s, before):
    assert vars(s.appointment) == before
    assert s.deposit.allocation_status == PaymentAllocationStatus.ACTIVE
    assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.bus.events == []
    assert not s.uow.committed


@pytest.mark.parametrize("role", ["owner", "admin"])
@pytest.mark.parametrize("case", ["retained", "past", "override", "transferable", "unconfirmed"])
def test_reschedule_success_returns_committed_state(route_scenario, role, case):
    advance = {"past": timedelta(days=-7), "transferable": timedelta(hours=48)}.get(
        case, timedelta(hours=24)
    )
    r = route_scenario(role=role, advance=advance)
    s = r.state
    if case == "unconfirmed":
        s.appointment.status = AppointmentStatus.QUOTED
        s.appointment.deposit_confirmed_at = None
    if case == "override":
        r.body.update(override_deposit_retention=True, deposit_override_reason="  Pedido do cliente  ")
    original_id = s.appointment.id
    with TestClient(app) as client:
        response = client.patch(r.url, json=r.body, headers=r.headers)
    assert response.status_code == 200
    retained = case in ("retained", "past")
    expected_status = "quoted" if retained or case == "unconfirmed" else "scheduled"
    body = response.json()
    assert body == {
        "appointment_id": str(original_id),
        "new_start_at": s.data.start_at.isoformat().replace("+00:00", "Z"),
        "new_end_at": s.data.end_at.isoformat().replace("+00:00", "Z"),
        "status": expected_status,
        "was_deposit_retained": retained,
        "deposit_override_applied": case == "override",
    }
    assert s.uow.committed
    assert len(s.bus.events) == 1
    event = s.bus.events[0]
    assert event.appointment_id == original_id
    assert event.was_deposit_retained is retained
    assert event.start_at == s.data.start_at
    logs = s.uow.audit_logs.find_many_by_entity_id(original_id)
    assert len(logs) == 1
    assert logs[0].actor_id == s.data.actor.id
    if case == "override":
        assert logs[0].changes["deposit_retention_override_reason"] == "Pedido do cliente"


@pytest.mark.parametrize("noop", [False, True])
def test_offset_dates_are_normalized_to_utc(route_scenario, noop):
    r = route_scenario()
    s = r.state
    start = s.appointment.start_at if noop else s.data.start_at
    end = s.appointment.end_at if noop else s.data.end_at
    offset = timezone(timedelta(hours=-3))
    r.body.update(
        new_start_at=start.astimezone(offset).isoformat(), new_end_at=end.astimezone(offset).isoformat()
    )
    response = TestClient(app).patch(r.url, json=r.body, headers=r.headers)
    assert response.status_code == 200
    assert response.json()["new_start_at"] == start.isoformat().replace("+00:00", "Z")
    assert response.json()["new_end_at"] == end.isoformat().replace("+00:00", "Z")
    if noop:
        assert not response.json()["was_deposit_retained"]
        assert not response.json()["deposit_override_applied"]
        assert s.bus.events == []
        assert s.uow.audit_logs.find_many_by_entity_id(s.appointment.id) == []
    assert s.uow.committed


@pytest.mark.parametrize("field", ["new_start_at", "new_end_at"])
@pytest.mark.parametrize("value", [None, "invalid", "2035-01-08T09:00:00"])
def test_invalid_or_naive_dates_are_rejected(route_scenario, field, value):
    r = route_scenario()
    before = vars(r.state.appointment).copy()
    r.body[field] = value
    response = TestClient(app).patch(r.url, json=r.body, headers=r.headers)
    assert response.status_code == 422
    assert any(error["loc"] == ["body", field] for error in response.json()["detail"])
    assert_rejected(r.state, before)


@pytest.mark.parametrize("case", ["missing_field", "invalid_uuid", "actor", "invalid_bool"])
def test_request_contract_rejects_invalid_input(route_scenario, case):
    r = route_scenario()
    before = vars(r.state.appointment).copy()
    if case == "missing_field":
        del r.body["new_end_at"]
    elif case == "invalid_uuid":
        r.url = "/appointments/not-a-uuid/reschedule"
    elif case == "actor":
        r.body["actor"] = {"id": str(uuid4()), "is_admin": True}
    else:
        r.body["override_deposit_retention"] = "not-a-boolean"
    response = TestClient(app).patch(r.url, json=r.body, headers=r.headers)
    assert response.status_code == 422
    assert_rejected(r.state, before)


@pytest.mark.parametrize("case", ["past", "present", "equal", "reversed"])
def test_invalid_interval_returns_validation_error(route_scenario, case):
    r = route_scenario()
    before = vars(r.state.appointment).copy()
    if case in ("past", "present"):
        r.body["new_start_at"] = (NOW - timedelta(days=case == "past")).isoformat()
    else:
        r.body["new_end_at"] = (r.state.data.start_at - timedelta(hours=case == "reversed")).isoformat()
    response = TestClient(app).patch(r.url, json=r.body, headers=r.headers)
    assert response.status_code == 422
    assert response.json() == {"detail": "reschedule_must_have_realistic_time_and_date"}
    assert_rejected(r.state, before)


@pytest.mark.parametrize(
    ("case", "status_code", "detail"),
    [
        ("invalid_token", 401, "invalid_credentials"),
        ("inactive", 403, "inactive_user"),
        ("other", 403, "unauthorized_user"),
        ("missing_header", 422, None),
    ],
)
def test_authentication_and_authorization(route_scenario, case, status_code, detail):
    r = route_scenario(role="other" if case == "other" else "owner")
    before = vars(r.state.appointment).copy()
    if case == "invalid_token":
        r.headers["Authorization"] = "Bearer invalid"
    elif case == "inactive":
        r.state.data.actor.is_active = False
    elif case == "missing_header":
        r.headers = {}
    response = TestClient(app).patch(r.url, json=r.body, headers=r.headers)
    assert response.status_code == status_code
    if detail:
        assert response.json() == {"detail": detail}
    assert_rejected(r.state, before)


@pytest.mark.parametrize("status", [AppointmentStatus.CANCELED, AppointmentStatus.COMPLETED])
def test_terminal_status_is_a_conflict(route_scenario, status):
    r = route_scenario()
    r.state.appointment.status = status
    before = vars(r.state.appointment).copy()
    response = TestClient(app).patch(r.url, json=r.body, headers=r.headers)
    assert response.status_code == 409
    assert response.json() == {"detail": "appointment_cannot_be_rescheduled_in_current_status"}
    assert_rejected(r.state, before)


def test_appointment_not_found(route_scenario):
    r = route_scenario()
    before = vars(r.state.appointment).copy()
    response = TestClient(app).patch(
        f"/appointments/{uuid4()}/reschedule", json=r.body, headers=r.headers
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "appointment_not_found"}
    assert_rejected(r.state, before)


@pytest.mark.parametrize(
    ("reason", "detail"),
    [
        (None, "deposit_override_reason_required"),
        ("  ", "deposit_override_reason_required"),
        ("abc", "deposit_override_reason_must_have_at_least_5_characters"),
        ("12345", "deposit_override_reason_must_contain_letters"),
    ],
)
def test_override_reason_errors(route_scenario, reason, detail):
    r = route_scenario()
    before = vars(r.state.appointment).copy()
    r.body.update(override_deposit_retention=True, deposit_override_reason=reason)
    response = TestClient(app).patch(r.url, json=r.body, headers=r.headers)
    assert response.status_code == 422
    assert response.json() == {"detail": detail}
    assert_rejected(r.state, before)


@pytest.mark.parametrize("case", ["missing_calendar", "blocked", "outside_hours", "occupied"])
def test_calendar_errors(
    route_scenario, monkeypatch, make_calendar_exception, make_scheduled_appointment, case
):
    r = route_scenario()
    s = r.state
    before = vars(s.appointment).copy()
    if case == "missing_calendar":
        monkeypatch.setattr(s.uow.calendar_settings, "find_by_user_id", lambda _: None)
    elif case == "blocked":
        s.uow.calendar_exceptions.create(
            make_calendar_exception(
                calendar_of_user=s.appointment.user_id,
                start_at=s.data.start_at,
                end_at=s.data.end_at,
                exception_type=CalendarExceptionType.BLOCK,
            )
        )
    elif case == "outside_hours":
        r.body.update(
            new_start_at=s.data.start_at.replace(hour=23).isoformat(),
            new_end_at=s.data.end_at.replace(hour=23, minute=30).isoformat(),
        )
    else:
        s.uow.appointments.create(
            make_scheduled_appointment(
                user_id=s.appointment.user_id,
                start_at=s.data.start_at,
                end_at=s.data.end_at,
            )
        )
    response = TestClient(app).patch(r.url, json=r.body, headers=r.headers)
    assert response.status_code == (409 if case == "occupied" else 400)
    assert response.json() == {
        "detail": (
            "the_time_slot_required_is_occupied"
            if case == "occupied"
            else "the_time_slot_required_is_not_available"
        )
    }
    assert_rejected(s, before)


@pytest.mark.parametrize("override", [False, True])
def test_inconsistent_deposit_is_internal_error(route_scenario, monkeypatch, override):
    r = route_scenario()
    before = vars(r.state.appointment).copy()
    monkeypatch.setattr(r.state.uow.payments, "find_many_by_appointment_id", lambda _: [])
    r.body.update(override_deposit_retention=override, deposit_override_reason="Pedido do cliente")
    response = TestClient(app).patch(r.url, json=r.body, headers=r.headers)
    assert response.status_code == 500
    assert response.json() == {"detail": "confirmed_deposit_without_active_payment"}
    assert_rejected(r.state, before)


def test_commit_failure_does_not_return_success_or_publish(route_scenario, monkeypatch):
    r = route_scenario()

    def fail_commit():
        raise RuntimeError("commit failed")

    monkeypatch.setattr(r.state.uow, "commit", fail_commit)
    response = TestClient(app, raise_server_exceptions=False).patch(
        r.url,
        json=r.body,
        headers=r.headers,
    )
    assert response.status_code == 500
    assert r.state.bus.events == []


@pytest.mark.parametrize(
    ("method", "error", "status_code", "detail"),
    [
        ("_get_recipient", AppointmentClientContactInfoCorruptedError, 500, "appointment_is_broken"),
        (
            "reschedule",
            AppointmentMustBeInCorrectPreviousStatusError,
            409,
            "appointment_cannot_be_rescheduled_in_current_status",
        ),
        ("calendar", SlotIsNotAvailableError, 400, "the_time_slot_required_is_not_available"),
    ],
)
def test_domain_failures_are_translated(route_scenario, monkeypatch, method, error, status_code, detail):
    r = route_scenario(advance=timedelta(days=3))

    def fail(*args, **kwargs):
        raise error()

    if method == "calendar":
        monkeypatch.setattr(type(r.state.use_case.calendar_policy), "can_reschedule", fail)
    else:
        monkeypatch.setattr(r.state.appointment, method, fail)
    before = vars(r.state.appointment).copy()
    response = TestClient(app).patch(r.url, json=r.body, headers=r.headers)
    assert response.status_code == status_code
    assert response.json() == {"detail": detail}
    assert_rejected(r.state, before)


def test_openapi_exposes_separate_cancel_and_reschedule_routes():
    schema = app.openapi()
    assert schema["paths"]["/appointments/{appointment_id}/cancel"]["patch"]["responses"].get("204")
    reschedule = schema["paths"]["/appointments/{appointment_id}/reschedule"]["patch"]
    assert reschedule["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/RescheduleAppointmentResponse"
    }

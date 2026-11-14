from copy import deepcopy
from uuid import uuid4

import pytest

from app.core.exceptions.appointments import (
    AppointmentProjectStateError,
    ProjectSessionAlreadyOccupiedError,
)
from app.core.types.appointment_enums import AppointmentStatus
from app.domain.studio.appointments.policies.appointment_project_policy import (
    AppointmentProjectPolicy,
)


@pytest.fixture
def policy():
    return AppointmentProjectPolicy()


@pytest.fixture
def canceled_session(make_appointment_base):
    return make_appointment_base(
        project_id=uuid4(),
        current_session=2,
        total_sessions=4,
        status=AppointmentStatus.CANCELED,
    )


@pytest.fixture
def project_appointment(
    make_appointment_base,
    make_quoted_appointment,
    make_scheduled_appointment,
    make_completed_appointment,
    canceled_session,
):
    def build(**overrides):
        values = {
            "project_id": canceled_session.project_id,
            "user_id": canceled_session.user_id,
            "client_info": canceled_session.client_info,
            "current_session": 2,
            "total_sessions": 4,
        }
        values.update(overrides)
        status = values.pop("status", AppointmentStatus.REQUESTED)
        factories = {
            AppointmentStatus.QUOTED: make_quoted_appointment,
            AppointmentStatus.SCHEDULED: make_scheduled_appointment,
            AppointmentStatus.COMPLETED: make_completed_appointment,
        }
        if status in factories:
            return factories[status](**values)
        return make_appointment_base(status=status, **values)

    return build


def test_allows_replacing_session_two_with_other_sessions_scheduled(
    policy, canceled_session, project_appointment
):
    """As sessões 1, 3 e 4 não ocupam a sessão 2 que queremos substituir."""
    appointments = [
        project_appointment(current_session=1, status=AppointmentStatus.COMPLETED),
        canceled_session,
        project_appointment(current_session=3, status=AppointmentStatus.SCHEDULED),
        project_appointment(current_session=4, status=AppointmentStatus.SCHEDULED),
    ]
    before = [vars(item).copy() for item in appointments]

    assert (
        policy.ensure_can_replace_session(appointment=canceled_session, appointments=appointments)
        is None
    )
    assert [vars(item) for item in appointments] == before


def test_allows_multiple_canceled_attempts_of_same_session(
    policy, canceled_session, project_appointment
):
    previous_attempt = project_appointment(status=AppointmentStatus.CANCELED)
    canceled_session.replaces_appointment_id = previous_attempt.id

    assert (
        policy.ensure_can_replace_session(
            appointment=canceled_session, appointments=[previous_attempt, canceled_session]
        )
        is None
    )


@pytest.mark.parametrize(
    "status",
    [
        AppointmentStatus.REQUESTED,
        AppointmentStatus.QUOTED,
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.COMPLETED,
    ],
)
def test_rejects_non_canceled_attempt_of_same_session_even_without_replacement_link(
    policy, canceled_session, project_appointment, status
):
    """Uma tentativa criada por outro fluxo também ocupa a sessão, inclusive concluída."""
    other = project_appointment(status=status)
    assert other.replaces_appointment_id is None

    with pytest.raises(ProjectSessionAlreadyOccupiedError):
        policy.ensure_can_replace_session(
            appointment=canceled_session, appointments=[canceled_session, other]
        )


def test_recognizes_original_by_id_when_loaded_as_another_object(policy, canceled_session):
    reloaded = deepcopy(canceled_session)
    assert reloaded is not canceled_session

    assert (
        policy.ensure_can_replace_session(appointment=canceled_session, appointments=[reloaded]) is None
    )


def test_rejects_empty_project_history(policy, canceled_session):
    with pytest.raises(AppointmentProjectStateError):
        policy.ensure_can_replace_session(appointment=canceled_session, appointments=[])


def test_rejects_history_missing_selected_appointment(policy, canceled_session, project_appointment):
    other = project_appointment(status=AppointmentStatus.CANCELED)
    with pytest.raises(AppointmentProjectStateError):
        policy.ensure_can_replace_session(appointment=canceled_session, appointments=[other])


@pytest.mark.parametrize("field", ["project_id", "current_session", "total_sessions"])
def test_rejects_selected_appointment_with_missing_project_data(policy, canceled_session, field):
    # Simula dados inconsistentes; a entidade normalmente rejeita esse estado na criação.
    setattr(canceled_session, field, None)
    with pytest.raises(AppointmentProjectStateError):
        policy.ensure_can_replace_session(appointment=canceled_session, appointments=[canceled_session])


def test_rejects_history_containing_another_project(policy, canceled_session, project_appointment):
    other_project = project_appointment(project_id=uuid4(), status=AppointmentStatus.CANCELED)
    with pytest.raises(AppointmentProjectStateError):
        policy.ensure_can_replace_session(
            appointment=canceled_session, appointments=[canceled_session, other_project]
        )


def test_rejects_inconsistent_project_total(policy, canceled_session, project_appointment):
    other = project_appointment(current_session=3, total_sessions=5)
    with pytest.raises(AppointmentProjectStateError):
        policy.ensure_can_replace_session(
            appointment=canceled_session, appointments=[canceled_session, other]
        )


def test_rejects_history_with_missing_session_number(policy, canceled_session, project_appointment):
    other = project_appointment(status=AppointmentStatus.CANCELED)
    other.current_session = None
    with pytest.raises(AppointmentProjectStateError):
        policy.ensure_can_replace_session(
            appointment=canceled_session, appointments=[canceled_session, other]
        )

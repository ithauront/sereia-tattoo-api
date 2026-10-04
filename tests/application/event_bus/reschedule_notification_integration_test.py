import asyncio
from dataclasses import replace
from datetime import timedelta

import pytest

from app.application.event_bus.setup import setup_event_bus
from app.core.types.appointment_enums import AppointmentStatus
from tests.application.use_cases.appointments import reschedule_appointment_test
from tests.fakes.fake_email_service import FakeEmailService

scenario = reschedule_appointment_test.scenario


@pytest.fixture
def pending_handlers(monkeypatch):
    tasks = []
    create_task = asyncio.create_task

    def track(coroutine):
        task = create_task(coroutine)
        tasks.append(task)
        return task

    monkeypatch.setattr("app.application.event_bus.integration_event_bus.asyncio.create_task", track)
    return tasks


@pytest.mark.parametrize("state", ["retained", "transferable", "override", "unconfirmed"])
async def test_use_case_event_reaches_registered_handler_after_commit(
    scenario,
    jwt_service_instance,
    pending_handlers,
    state,
):
    s = scenario(advance=timedelta(days=3) if state == "transferable" else timedelta(days=1))
    if state == "unconfirmed":
        s.appointment.status = AppointmentStatus.QUOTED
        s.appointment.deposit_confirmed_at = None

    class CommittedEmailService(FakeEmailService):
        async def send_email(self, to, subject, html_content):
            assert s.uow.committed
            assert s.appointment.start_at == s.data.start_at
            assert len(s.uow.audit_logs.find_many_by_entity_id(s.appointment.id)) == 1
            await super().send_email(to, subject, html_content)

    service = CommittedEmailService()
    _, bus = setup_event_bus(service, jwt_service_instance)
    s.use_case.integration_bus = bus
    result = await s.use_case.execute(
        replace(
            s.data,
            override_deposit_retention=state == "override",
            deposit_override_reason="Pedido do cliente" if state == "override" else None,
        )
    )
    assert len(pending_handlers) == 1
    await asyncio.gather(*pending_handlers)
    assert len(service.sent_emails) == 2
    artist = next(email for email in service.sent_emails if email["to"] == s.data.actor.email)
    client = next(
        email for email in service.sent_emails if email["to"] == s.appointment.client_info.email
    )
    assert str(result.appointment_id) in artist["html"]
    assert result.start_at.strftime("%d/%m/%Y") in client["html"]
    if state == "retained":
        assert "CAUÇÃO RETIDA" in artist["html"]
        assert result.was_deposit_retained
    elif state == "unconfirmed":
        assert "SEM CAUÇÃO CONFIRMADA" in artist["html"]
    else:
        assert "CAUÇÃO MANTIDA" in artist["html"]
        assert result.deposit_override_applied is (state == "override")


@pytest.mark.parametrize("commit_failure", [False, True])
async def test_registered_bus_sends_nothing_for_noop_or_failed_commit(
    scenario,
    jwt_service_instance,
    pending_handlers,
    monkeypatch,
    commit_failure,
):
    s = scenario()
    service = FakeEmailService()
    _, s.use_case.integration_bus = setup_event_bus(service, jwt_service_instance)
    if commit_failure:

        def fail_commit():
            raise RuntimeError("commit failed")

        monkeypatch.setattr(s.uow, "commit", fail_commit)
        with pytest.raises(RuntimeError, match="commit failed"):
            await s.use_case.execute(s.data)
    else:
        await s.use_case.execute(
            replace(
                s.data,
                start_at=s.appointment.start_at,
                end_at=s.appointment.end_at,
            )
        )
    assert pending_handlers == []
    assert service.sent_emails == []

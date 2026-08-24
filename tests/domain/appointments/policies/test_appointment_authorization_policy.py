from uuid import uuid4

import pytest

from app.core.exceptions.appointments import OnlyAdminOrOwnerOfAppointmentError
from app.domain.studio.appointments.policies.appointment_authorization_policy import (
    AppointmentAuthorizationPolicy,
)


def test_ensure_admin_not_owner_should_not_raise(make_user, write_uow, make_appointment_base):
    admin = make_user(is_admin=True)
    write_uow.users.create(admin)

    appointment = make_appointment_base(user_id=uuid4())
    write_uow.appointments.create(appointment)

    policy = AppointmentAuthorizationPolicy()

    test_policy = policy.ensure_admin_or_owner(actor=admin, appointment=appointment)

    assert test_policy is None


def test_ensure_owner_not_admin_should_not_raise(make_user, write_uow, make_appointment_base):
    user = make_user(is_admin=False)
    write_uow.users.create(user)

    appointment = make_appointment_base(user_id=user.id)
    write_uow.appointments.create(appointment)

    policy = AppointmentAuthorizationPolicy()

    test_policy = policy.ensure_admin_or_owner(actor=user, appointment=appointment)

    assert test_policy is None


def test_ensure_different_user_should_raise(make_user, write_uow, make_appointment_base):
    user = make_user(is_admin=False)
    write_uow.users.create(user)

    appointment = make_appointment_base(user_id=uuid4())
    write_uow.appointments.create(appointment)

    policy = AppointmentAuthorizationPolicy()

    with pytest.raises(OnlyAdminOrOwnerOfAppointmentError):
        policy.ensure_admin_or_owner(actor=user, appointment=appointment)

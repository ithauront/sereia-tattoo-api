from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.event_bus.transactional_event_bus import TransactionalEventBus
from app.application.notifications.handlers.send_activation_confirmation_email import (
    SendActivationConfirmationEmailHandler,
)
from app.application.notifications.handlers.send_password_reset_email import (
    SendPasswordResetEmailHandler,
)
from app.application.notifications.handlers.send_user_activation_email import (
    SendUserActivationHandler,
)
from app.application.notifications.handlers.send_vip_client_creation_notification_email import (
    SendVipClientCreationNotificationEmailHandler,
)
from app.application.studio.handlers.add_credits_from_completed_appointment import (
    AddCreditsFromCompletedAppointmentHandler,
)
from app.core.security.versioned_token_service import VersionedTokenService
from app.domain.studio.appointments.events.appointment_completed import (
    AppointmentCompleted,
)
from app.domain.studio.users.events.activation_email_requested import (
    ActivationEmailRequested,
)
from app.domain.studio.users.events.create_vip_client_email_requested import (
    CreateVipClientEmailRequested,
)
from app.domain.studio.users.events.password_reset_email_requested import (
    PasswordResetEmailRequested,
)
from app.domain.studio.users.events.send_action_made_email_requested import (
    SendActionMadeEmailRequested,
)


def setup_event_bus(
    email_service,
    token_service,
):

    activation_token_service = VersionedTokenService(
        jwt_service=token_service, token_type="activation", ttl_minutes=60
    )

    password_token_service = VersionedTokenService(
        jwt_service=token_service, token_type="reset_password", ttl_minutes=15
    )

    transactional_bus = TransactionalEventBus()
    integration_bus = IntegrationEventBus()

    integration_bus.register(
        ActivationEmailRequested,
        SendUserActivationHandler(email_service=email_service, token_service=activation_token_service),
    )

    integration_bus.register(
        PasswordResetEmailRequested,
        SendPasswordResetEmailHandler(email_service=email_service, token_service=password_token_service),
    )

    integration_bus.register(
        CreateVipClientEmailRequested,
        SendVipClientCreationNotificationEmailHandler(email_service=email_service),
    )

    integration_bus.register(
        SendActionMadeEmailRequested,
        SendActivationConfirmationEmailHandler(email_service=email_service),
    )

    transactional_bus.register(
        AppointmentCompleted,
        AddCreditsFromCompletedAppointmentHandler(),
    )

    return transactional_bus, integration_bus

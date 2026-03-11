from app.application.event_bus.event_bus import EventBus
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)
from app.core.exceptions.users import UserActivatedBeforeError, UserNotFoundError
from app.core.normalize.normalize_email import normalize_email


class PrepareResendActivationEmailUseCase:
    def __init__(self, uow: WriteUnitOfWork, event_bus: EventBus):
        self.uow = uow
        self.event_bus = event_bus

    async def execute(self, data: PrepareResendActivationEmailInput) -> None:
        with self.uow:
            email = normalize_email(data.user_email)

            user = self.uow.users.find_by_email(email)

            if not user:
                raise UserNotFoundError()

            if user.has_activated_once:
                raise UserActivatedBeforeError()

            event = user.request_activation_email()

        await self.event_bus.publish(event)

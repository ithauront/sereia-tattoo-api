from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.api.dependencies.actor_id import get_optional_actor_id
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.events import get_integration_event_bus, get_transactional_event_bus
from app.api.dependencies.policies import get_calendar_policy
from app.api.dependencies.write_unit_of_work import (
    get_write_unit_of_work,
)
from app.api.schemas.appointments import CreateAppointmentRequest
from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.event_bus.transactional_event_bus import TransactionalEventBus
from app.application.studio.unit_of_work.write_unit_of_work import (
    WriteUnitOfWork,
)
from app.application.studio.use_cases.appointments_use_cases.complete_paid_appointment_use_case import (
    CompletePaidAppointmentUseCase,
)
from app.application.studio.use_cases.appointments_use_cases.create_appointment_use_case import (
    CreateAppointmentUseCase,
)
from app.application.studio.use_cases.DTO.complete_paid_appointment_dto import (
    CompletePaidAppointmentInput,
)
from app.application.studio.use_cases.DTO.create_appointment_dto import CreateAppointmentInput
from app.core.exceptions.appointments import (
    AppointmentMustBeScheduledError,
    AppointmentNotFoundError,
    AppointmentWasNotFullyPaidError,
    SlotIsAlreadyOccupiedError,
    SlotIsNotAvailableError,
)
from app.core.exceptions.calendar import (
    CannotFindWorkingPeriodsForThisUserError,
    UserIsNotWorkingInDesignatedTimeframeError,
)
from app.core.exceptions.clients import ClientInfoModelError
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)
from app.domain.studio.value_objects.client_code import ClientCode

router = APIRouter(prefix="/appointments")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: CreateAppointmentRequest,
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    integration_bus: IntegrationEventBus = Depends(get_integration_event_bus),
    actor_id: UUID | None = Depends(get_optional_actor_id),
    calendar_policy: CalendarAvailabilityPolicy = Depends(get_calendar_policy),
):
    try:
        client_info = ClientInfo(
            vip_client_id=data.vip_client_id,
            name=data.name,
            email=data.email,
            phone=data.phone,
        )
        referral_code = ClientCode(data.referral_code) if data.referral_code else None

        use_case = CreateAppointmentUseCase(
            integration_bus=integration_bus, uow=uow, calendar_policy=calendar_policy
        )
        dto = CreateAppointmentInput(
            appointment_type=data.appointment_type,
            user_id=data.user_id,
            client_info=client_info,
            start_at=data.start_at,
            end_at=data.end_at,
            placement=data.placement,
            color=data.color,
            details=data.details,
            size=data.size,
            referral_code=referral_code,
            actor_id=actor_id,
        )

        await use_case.execute(dto)

    except (
        CannotFindWorkingPeriodsForThisUserError,
        UserIsNotWorkingInDesignatedTimeframeError,
        SlotIsNotAvailableError,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="the_time_slot_required_is_not_available",
        )

    except SlotIsAlreadyOccupiedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="the_time_slot_required_is_occupied",
        )

    except ClientInfoModelError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )


@router.patch("/{appointment_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_paid_appointment(
    appointment_id: UUID,
    current_user=Depends(get_current_active_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    transactional_bus: TransactionalEventBus = Depends(get_transactional_event_bus),
):
    try:
        use_case = CompletePaidAppointmentUseCase(uow=uow, transactional_bus=transactional_bus)
        dto = CompletePaidAppointmentInput(appointment_id=appointment_id, actor_id=current_user.id)

        await use_case.execute(dto)
    except AppointmentMustBeScheduledError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="only_appointments_in_scheduled_status_can_be_completed",
        )
    except AppointmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="appointment_not_found")
    except AppointmentWasNotFullyPaidError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="appointment_was_not_fully_paid_check_payments_and_possible_refunds",
        )

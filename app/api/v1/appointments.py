from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from app.application.event_bus.transactional_event_bus import TransactionalEventBus
from app.application.studio.unit_of_work.write_unit_of_work import (
    WriteUnitOfWork,
)
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.events import get_transactional_event_bus
from app.api.dependencies.write_unit_of_work import (
    get_write_unit_of_work,
)
from app.application.studio.use_cases.appointments_use_cases.complete_paid_appointment_use_case import (
    CompletePaidAppointmentUseCase,
)
from app.application.studio.use_cases.DTO.complete_paid_appointment_dto import (
    CompletePaidAppointmentInput,
)
from app.core.exceptions.appointments import (
    AppointmentMustBeScheduledError,
    AppointmentNotFoundError,
    AppointmentWasNotFullyPaidError,
)

router = APIRouter(prefix="/appointments")


@router.patch("/{appointment_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_paid_appointment(
    appointment_id: UUID,
    current_user=Depends(get_current_active_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    transactional_bus: TransactionalEventBus = Depends(get_transactional_event_bus),
):
    try:
        use_case = CompletePaidAppointmentUseCase(
            uow=uow, transactional_bus=transactional_bus
        )
        dto = CompletePaidAppointmentInput(
            appointment_id=appointment_id, actor_id=current_user.id
        )

        await use_case.execute(dto)
    except AppointmentMustBeScheduledError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="only_appointments_in_scheduled_status_can_be_completed",
        )
    except AppointmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="appointment_not_found"
        )
    except AppointmentWasNotFullyPaidError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="appointment_was_not_fully_paid_check_payments_and_possible_refunds",
        )

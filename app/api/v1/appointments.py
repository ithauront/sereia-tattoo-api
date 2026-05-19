from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from app.application.event_bus.event_bus import EventBus
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.unit_of_work.write_unit_of_work import (
    WriteUnitOfWork,
)
from app.api.dependencies.auth import (
    get_current_active_user,
    get_current_admin_user,
)
from app.api.dependencies.events import get_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import (
    get_write_unit_of_work,
)
from app.application.studio.use_cases.appointments_use_cases.complete_paid_appointment_use_case import CompletePaidAppointmentUseCase
from app.application.studio.use_cases.DTO.complete_paid_appointment_dto import CompletePaidAppointmentInput
from app.core.exceptions.appointments import AppointmentNotFoundError, AppointmentWasNotFullyPaidError

router = APIRouter(prefix="/appointments")

@router.patch("/{appointment_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_paid_appointment(
    appointment_id: UUID,
    current_user=Depends(get_current_active_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    event_bus: EventBus = Depends(get_event_bus),
):
    try:
        use_case = CompletePaidAppointmentUseCase(uow=uow, event_bus=event_bus)
        dto= CompletePaidAppointmentInput(appointment_id=appointment_id, actor_id=current_user.id)

        await use_case.execute(dto)

    except AppointmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="appointment_not_found"
        )
    except AppointmentWasNotFullyPaidError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="appointment_was_not_fully_paid_check_payments_and_possible_refunds",
        )
    

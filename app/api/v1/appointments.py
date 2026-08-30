from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from app.api.dependencies.actor_id import get_optional_actor_id
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.events import get_integration_event_bus, get_transactional_event_bus
from app.api.dependencies.policies import get_appointment_authorization_policy, get_calendar_policy
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import (
    get_write_unit_of_work,
)
from app.api.schemas.appointments import CreateAppointmentRequest, QuoteAppointmentRequest
from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.event_bus.transactional_event_bus import TransactionalEventBus
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.unit_of_work.write_unit_of_work import (
    WriteUnitOfWork,
)
from app.application.studio.use_cases.appointments_use_cases.complete_paid_appointment_use_case import (
    CompletePaidAppointmentUseCase,
)
from app.application.studio.use_cases.appointments_use_cases.create_appointment_use_case import (
    CreateAppointmentUseCase,
)
from app.application.studio.use_cases.appointments_use_cases.quote_appointment_use_case import (
    QuoteAppointmentUseCase,
)
from app.application.studio.use_cases.DTO.complete_paid_appointment_dto import (
    CompletePaidAppointmentInput,
)
from app.application.studio.use_cases.DTO.create_appointment_dto import CreateAppointmentInput
from app.application.studio.use_cases.DTO.quote_appointement_dto import QuoteAppointmentInput
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.appointments.policies.appointment_authorization_policy import (
    AppointmentAuthorizationPolicy,
)
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)
from app.domain.studio.value_objects.client_code import ClientCode

router = APIRouter(prefix="/appointments")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: CreateAppointmentRequest,
    write_uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    read_uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
    integration_bus: IntegrationEventBus = Depends(get_integration_event_bus),
    actor_id: UUID | None = Depends(get_optional_actor_id),
    calendar_policy: CalendarAvailabilityPolicy = Depends(get_calendar_policy),
):
    client_info = ClientInfo(
        vip_client_id=data.vip_client_id,
        name=data.name,
        email=data.email,
        phone=data.phone,
    )
    referral_code = ClientCode(data.referral_code) if data.referral_code else None

    use_case = CreateAppointmentUseCase(
        integration_bus=integration_bus,
        write_uow=write_uow,
        read_uow=read_uow,
        calendar_policy=calendar_policy,
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


@router.patch("/{appointment_id}/quote", status_code=status.HTTP_204_NO_CONTENT)
async def quote_appointment(
    appointment_id: UUID,
    data: QuoteAppointmentRequest,
    current_user=Depends(get_current_active_user),
    write_uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    read_uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
    integration_bus: IntegrationEventBus = Depends(get_integration_event_bus),
    authorization_policy: AppointmentAuthorizationPolicy = Depends(get_appointment_authorization_policy),
):
    use_case = QuoteAppointmentUseCase(
        read_uow=read_uow,
        write_uow=write_uow,
        integration_bus=integration_bus,
        appointment_authorization_policy=authorization_policy,
    )
    dto = QuoteAppointmentInput(price=data.price, actor=current_user, appointment_id=appointment_id)

    await use_case.execute(dto)


@router.patch("/{appointment_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_paid_appointment(
    appointment_id: UUID,
    current_user=Depends(get_current_active_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    transactional_bus: TransactionalEventBus = Depends(get_transactional_event_bus),
):
    use_case = CompletePaidAppointmentUseCase(uow=uow, transactional_bus=transactional_bus)
    dto = CompletePaidAppointmentInput(appointment_id=appointment_id, actor_id=current_user.id)

    await use_case.execute(dto)

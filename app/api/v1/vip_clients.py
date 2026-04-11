from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import get_current_active_user, get_current_admin_user
from app.api.dependencies.events import get_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.api.schemas.user import (
    ChangeVipClientEmailRequest,
    ChangeVipClientPhoneRequest,
    CreateVipClientRequest,
    CreateVipClientResponse,
    GenerateVipClientCodeRequest,
    GenerateVipClientCodeResponse,
)
from app.application.studio.services.client_code_generator import ClientCodeGenerator
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.change_email_dto import (
    ChangeVipClientEmailInput,
)
from app.application.studio.use_cases.DTO.change_phone_dto import (
    ChangeVipClientPhoneInput,
)
from app.application.studio.use_cases.DTO.commun import Direction
from app.application.studio.use_cases.DTO.create_vip_client_dto import (
    CreateVipClientInput,
)
from app.application.studio.use_cases.DTO.get_users_dto import (
    GetVipClientInput,
    ListVipClientsInput,
    ListVipClientsOutput,
    VipClientsOrderBy,
)
from app.application.studio.use_cases.DTO.vip_client_output import (
    VipClientOutputWithDetails,
)
from app.application.studio.use_cases.users_use_cases.change_vip_client_email import (
    ChangeVipClientEmailUseCase,
)
from app.application.studio.use_cases.users_use_cases.change_vip_client_phone import (
    ChangeVipClientPhoneUseCase,
)
from app.application.studio.use_cases.users_use_cases.create_vip_client import (
    CreateVipClientUseCase,
)
from app.application.studio.use_cases.users_use_cases.generate_vip_client_code import (
    GenerateVipClientCodeUseCase,
)
from app.application.studio.use_cases.users_use_cases.get_vip_client import (
    GetVipClientUseCase,
)
from app.application.studio.use_cases.users_use_cases.list_vip_clients import (
    ListVipClientsUseCase,
)
from app.core.exceptions.users import (
    AllClientCodesTakenError,
    ClientCodeAlreadyTakenError,
    EmailAlreadyTakenError,
    PhoneAlreadyTakenError,
    VipClientNotFoundError,
)
from app.core.exceptions.validation import ValidationError


router = APIRouter(prefix="/vip-clients")


@router.post(
    "/generate-client-codes",
    status_code=status.HTTP_200_OK,
    response_model=GenerateVipClientCodeResponse,
)
def generate_vip_client_code_suggestions(
    data: GenerateVipClientCodeRequest,
    current_user=Depends(get_current_admin_user),
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
):
    generator = ClientCodeGenerator(uow)
    use_case = GenerateVipClientCodeUseCase(generator=generator)

    try:
        codes = use_case.execute(data.name)
        return {"codes": [str(code) for code in codes]}
    except AllClientCodesTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="please_try_creating_client_code_with_last_name",
        )


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=CreateVipClientResponse
)
async def create_vip_client(
    data: CreateVipClientRequest,
    current_user=Depends(get_current_admin_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    event_bus=Depends(get_event_bus),
):
    try:
        use_case = CreateVipClientUseCase(uow, event_bus)
        dto = CreateVipClientInput(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            client_code=data.client_code,
        )

        await use_case.execute(dto)

    except EmailAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email_already_taken",
        )
    except PhoneAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="phone_already_taken",
        )
    except ClientCodeAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="client_code_already_taken_please_generate_another",
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )

    return {"message": "VIP Client created"}


@router.patch("/{vip_client_id}/change-email", status_code=status.HTTP_204_NO_CONTENT)
def change_vip_client_email(
    data: ChangeVipClientEmailRequest,
    vip_client_id: UUID,
    current_user=Depends(get_current_admin_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
):
    use_case = ChangeVipClientEmailUseCase(uow)
    dto = ChangeVipClientEmailInput(
        vip_client_id=vip_client_id, new_email=data.new_email
    )

    try:
        use_case.execute(dto)
    except VipClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="vip_client_not_found"
        )
    except EmailAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email_chosen_is_already_taken"
        )


@router.patch("/{vip_client_id}/change-phone", status_code=status.HTTP_204_NO_CONTENT)
def change_vip_client_phone(
    data: ChangeVipClientPhoneRequest,
    vip_client_id: UUID,
    current_user=Depends(get_current_admin_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
):
    use_case = ChangeVipClientPhoneUseCase(uow)
    dto = ChangeVipClientPhoneInput(
        vip_client_id=vip_client_id, new_phone=data.new_phone
    )

    try:
        use_case.execute(dto)
    except VipClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="vip_client_not_found"
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )
    except PhoneAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="phone_chosen_is_already_taken"
        )


@router.get("", status_code=status.HTTP_200_OK, response_model=ListVipClientsOutput)
def list_vip_clients(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    order_by: VipClientsOrderBy = VipClientsOrderBy.first_name,
    direction: Direction = Direction.asc,
    current_user=Depends(get_current_active_user),
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
):
    use_case = ListVipClientsUseCase(uow)
    dto = ListVipClientsInput(
        page=page,
        limit=limit,
        order_by=order_by,
        direction=direction,
    )

    result = use_case.execute(dto)

    return result


@router.get(
    "/{vip_client_id}",
    status_code=status.HTTP_200_OK,
    response_model=VipClientOutputWithDetails,
)
def get_vip_client(
    vip_client_id: UUID,
    current_user=Depends(get_current_active_user),
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
):
    use_case = GetVipClientUseCase(uow)
    dto = GetVipClientInput(vip_client_id=vip_client_id)

    try:
        return use_case.execute(dto)

    except VipClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="vip_client_not_found"
        )

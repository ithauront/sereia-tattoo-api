from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError

from app.api.dependencies.auth import get_current_active_user, get_current_admin_user
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.api.schemas.client_credit_entries import (
    AddClientCreditsRequest,
    AddClientCreditsResponse,
)
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.add_client_credits import (
    AddClientCreditByAdminInput,
)
from app.application.studio.use_cases.DTO.commun import Direction
from app.application.studio.use_cases.DTO.get_client_credit_entries import (
    CreditEntryDetailsOutput,
    GetCreditEntryDetailsByIdInput,
)
from app.application.studio.use_cases.DTO.list_client_credit_entries import (
    ListCreditEntriesByClientIdInput,
    ListCreditEntriesOutput,
)
from app.application.studio.use_cases.finances_use_cases.add_client_credit_by_admin import (
    AddClientCreditByAdminUseCase,
)
from app.application.studio.use_cases.finances_use_cases.get_credit_entry_details_by_id import (
    GetCreditEntryDetailsByIdUseCase,
)
from app.application.studio.use_cases.finances_use_cases.list_credit_entries_by_client_id import (
    ListCreditEntriesByClientIdUseCase,
)
from app.core.exceptions.marketing import (
    CreditEntryNotFoundError,
    CreditMustBePositiveError,
)
from app.core.exceptions.users import UserNotFoundError, VipClientNotFoundError

router = APIRouter(prefix="/client-credit-entries")


# TODO: fazer teste dessa rota
#TODO: verificar se deixamos o add credits no nome da toda uma vez que ela ja é post"/client-credit-entries/{vip_client_id}/add_credits" o post ja pode ser semantico de dizer que adiciona credito. mas talvez colocar by_admin no lugar de add credits
@router.post(
    "/{vip_client_id}/add_credits",
    status_code=status.HTTP_201_CREATED,
    response_model=AddClientCreditsResponse,
)
def add_client_credits_by_admin(
    data: AddClientCreditsRequest,
    vip_client_id: UUID,
    current_user=Depends(get_current_admin_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
):
    use_case = AddClientCreditByAdminUseCase(uow)
    dto = AddClientCreditByAdminInput(
        vip_client_id=vip_client_id,
        actor_id=current_user.id,
        quantity=data.quantity,
        reason=data.reason,
    )

    try:
        result = use_case.execute(dto)
    except VipClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="vip_client_not_found",
        )
    except CreditMustBePositiveError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_credit_quantity"
        )

    return {
        "vip_client": vip_client_id,
        "quantity_added": data.quantity,
        "total_credits_before": result.before,
        "total_credits_after": result.after,
    }


@router.get(
    "/by-id/{credit_entry_id}",
    status_code=status.HTTP_200_OK,
    response_model=CreditEntryDetailsOutput,
)
def get_credit_entry_by_id(
    credit_entry_id: UUID,
    current_user=Depends(get_current_active_user),
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
):
    use_case = GetCreditEntryDetailsByIdUseCase(uow)
    dto = GetCreditEntryDetailsByIdInput(client_credit_id=credit_entry_id)

    try:
        return use_case.execute(dto)
    except CreditEntryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="client_credit_entry_not_found",
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="credit_came_from_an_admin_operation_but_admin_not_found",
        )
    except VipClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="client_credit_entry_in_not_attached_to_a_vip_client",
        )


@router.get(
    "/by-client/{vip_client_id}",
    status_code=status.HTTP_200_OK,
    response_model=ListCreditEntriesOutput,
)
def list_credit_entries_by_vip_client_id(
    vip_client_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    direction: Direction = Direction.asc,
    current_user=Depends(get_current_active_user),
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
):
    use_case = ListCreditEntriesByClientIdUseCase(uow)
    dto = ListCreditEntriesByClientIdInput(
        vip_client_id=vip_client_id, page=page, limit=limit, direction=direction
    )

    try:
        return use_case.execute(dto)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )

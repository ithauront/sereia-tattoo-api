from fastapi import (
    APIRouter,
    Depends,
    status,
)

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.events import get_integration_event_bus, get_transactional_event_bus
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.api.schemas.payments import CreatePaymentRequest, CreatePaymentResponse
from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.event_bus.transactional_event_bus import TransactionalEventBus
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.payment_dto import CreatePaymentInput
from app.application.studio.use_cases.finances_use_cases.create_payment_use_case import (
    CreatePaymentUseCase,
)

router = APIRouter(prefix="/payments")


# TODO: completar os testes de integração do fluxo de criação de pagamentos:
# - atravessar HTTP + autenticação real + SQLAlchemy + commit usando um PostgreSQL de teste;
# - atravessar a rota de caução até ConfirmDepositHandler e o envio do e-mail ao cliente;
# - repetir o fluxo de caução para appointment cujo contato vem de um VIP client;
# - validar concorrência real para idempotency_key, external_reference e saldo de créditos;
# - executar as migrations em banco vazio e criar pagamentos de todos os métodos/propósitos.
@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreatePaymentResponse)
async def create_payment(
    data: CreatePaymentRequest,
    current_user=Depends(get_current_active_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    integration_bus: IntegrationEventBus = Depends(get_integration_event_bus),
    transactional_bus: TransactionalEventBus = Depends(get_transactional_event_bus),
):
    use_case = CreatePaymentUseCase(
        uow=uow, transactional_event_bus=transactional_bus, integration_event_bus=integration_bus
    )

    dto = CreatePaymentInput(
        idempotency_key=data.idempotency_key,
        actor=current_user,
        amount=data.amount,
        payment_method=data.payment_method,
        payment_purpose=data.payment_purpose,
        appointment_id=data.appointment_id,
        credit_owner_vip_client_id=data.credit_owner_vip_client_id,
        description=data.description,
        external_reference=data.external_reference,
    )

    result = await use_case.execute(data=dto)

    response = CreatePaymentResponse(
        payment_id=result.payment_id,
        amount=result.amount,
        payment_method=result.payment_method,
        payment_purpose=result.payment_purpose,
        appointment_id=result.appointment_id,
        vip_client_id=result.vip_client_id,
        created_at=result.created_at,
    )

    return response

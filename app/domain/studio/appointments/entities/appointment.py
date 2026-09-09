from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from app.core.exceptions.appointments import (
    AppointmentClientContactInfoCorruptedError,
    AppointmentMustBeInCorrectPreviousStatusError,
    AppointmentMustBeScheduledError,
    AppointmentMustHaveAClientContactInfo,
    AppointmentMustHaveRealisticTimeAndDateError,
    AppointmentProjectStateError,
    AppointmentStatusBreakingDomainRules,
    AppointmentWasNotFullyPaidError,
    CurrentSessionMustBeLessThanTotalError,
    CurrentSessionMustBePositiveError,
    ForMultipleSessionsProjectIdMustBeDefinedError,
    PriceMustBeDefinedError,
    PriceMustBePositiveError,
    TotalSessionsMustBeAtLeastTwoError,
    TotalSessionsMustMatchProjectError,
    TotalSessionsNumberMustBeDefineError,
    TotalSessionsNumberMustBePositiveError,
)
from app.core.types.appointment_enums import (
    AppointmentStatus,
    AppointmentType,
)
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.appointments.events.appointment_completed import (
    AppointmentCompleted,
)
from app.domain.studio.appointments.events.create_appointment_request import (
    CreateAppointmentEmailRequested,
)
from app.domain.studio.appointments.events.notify_of_appointment_quoted import (
    NotifyOfAppointmentQuoted,
)
from app.domain.studio.value_objects.client_code import ClientCode
from app.domain.utils.ensure_enum import ensure_enum


class Appointment:
    def __init__(
        self,
        *,
        id: UUID | None = None,
        status: AppointmentStatus,
        appointment_type: AppointmentType,
        project_id: UUID | None = None,
        user_id: UUID,
        start_at: datetime,
        end_at: datetime,
        placement: str,
        details: str,
        size: str | None = None,
        current_session: int | None = None,
        total_sessions: int | None = None,
        color: bool = False,
        price: Decimal | None = None,
        deposit_confirmed_at: datetime | None = None,
        client_info: ClientInfo,
        referral_code: ClientCode | None = None,
        is_posted_on_socials: bool = False,
        observations: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        now = self._utc_now()

        self.id = id or uuid4()
        self.status = ensure_enum(status, AppointmentStatus)
        self.appointment_type = ensure_enum(appointment_type, AppointmentType)
        self.project_id = project_id
        self.user_id = user_id
        self.start_at = start_at
        self.end_at = end_at
        self.placement = placement
        self.details = details
        self.size = size
        self.current_session = current_session
        self.total_sessions = total_sessions
        self.color = color
        self.price = price
        self.deposit_confirmed_at = deposit_confirmed_at
        self.client_info = client_info
        self.referral_code = referral_code
        self.is_posted_on_socials = is_posted_on_socials
        self.observations = observations
        self.created_at = created_at or now
        self.updated_at = updated_at or now

        self._validate_state()

    @classmethod
    def create(
        cls,
        *,
        appointment_type: AppointmentType,
        project_id: UUID | None = None,
        user_id: UUID,
        start_at: datetime,
        end_at: datetime,
        placement: str,
        details: str,
        size: str | None = None,
        current_session: int | None = None,
        total_sessions: int | None = None,
        color: bool = False,
        client_info: ClientInfo,
        referral_code: ClientCode | None = None,
    ) -> "Appointment":
        if end_at <= start_at:
            raise AppointmentMustHaveRealisticTimeAndDateError()
        if client_info.email is None and client_info.vip_client_id is None:
            raise AppointmentMustHaveAClientContactInfo()

        return cls(
            status=AppointmentStatus.REQUESTED,
            appointment_type=appointment_type,
            project_id=project_id,
            user_id=user_id,
            start_at=start_at,
            end_at=end_at,
            placement=placement,
            details=details,
            size=size,
            total_sessions=total_sessions,
            current_session=current_session,
            color=color,
            client_info=client_info,
            referral_code=referral_code,
        )

    def set_price(self, price: Decimal):
        """
        we usualy will use quote method.
        set_price is used by the owner/admin for exceptional price changes after quoting,
        without changing the appointment status.
        """
        if price <= 0:
            raise PriceMustBePositiveError()

        self.price = price
        self._touch()

    def set_sessions_total(self, total_sessions: int):
        self._validate_total_sessions_value(total_sessions)
        if total_sessions > 1 and self.project_id is None:
            raise ForMultipleSessionsProjectIdMustBeDefinedError()
        if self.project_id is not None and total_sessions < 2:
            raise AppointmentProjectStateError()
        if self.current_session is not None and total_sessions < self.current_session:
            raise CurrentSessionMustBeLessThanTotalError()

        self.total_sessions = total_sessions

        if self.current_session is None:
            self.current_session = 1

        self._touch()

    def set_current_session(self, current_session: int):
        if not self.total_sessions:
            raise TotalSessionsNumberMustBeDefineError()
        if self.total_sessions > 1 and self.project_id is None:
            raise ForMultipleSessionsProjectIdMustBeDefinedError()
        if current_session < 1:
            raise CurrentSessionMustBePositiveError()
        if current_session > self.total_sessions:
            raise CurrentSessionMustBeLessThanTotalError()
        self.current_session = current_session
        self._touch()

    def update_total_sessions(self, new_total_session: int):
        """new total_sessions can be less than total_sessions if we realise
        it will take less appointments to end an project,
        same aplies for new total session grater than before"""
        # TODO: in the use_case that will update total sessions we need to update form all appointments
        # linked by the project id
        if new_total_session == self.total_sessions:
            return
        self._validate_total_sessions_value(new_total_session)
        if new_total_session > 1 and self.project_id is None:
            raise ForMultipleSessionsProjectIdMustBeDefinedError()
        if self.project_id is not None and new_total_session < 2:
            raise AppointmentProjectStateError()
        if self.current_session is not None and new_total_session < self.current_session:
            raise CurrentSessionMustBeLessThanTotalError()

        self.total_sessions = new_total_session
        self._touch()

    def update_color(self, color: bool):
        self.color = color
        self._touch()

    def mark_as_posted_on_socials(self):
        self.is_posted_on_socials = True
        self._touch()

    def quote(self, price: Decimal, total_sessions: int | None = None):
        if self.status != AppointmentStatus.REQUESTED:
            raise AppointmentMustBeInCorrectPreviousStatusError()
        if price <= 0:
            raise PriceMustBePositiveError()
        self._configure_project_for_quote(total_sessions)

        self.price = price
        self.status = AppointmentStatus.QUOTED
        self._touch()

    def _configure_project_for_quote(self, total_sessions: int | None) -> None:
        if total_sessions is None:
            return

        self._validate_total_sessions_value(total_sessions)

        has_no_project_data = (
            self.project_id is None and self.current_session is None and self.total_sessions is None
        )
        if has_no_project_data:
            self.project_id = uuid4()
            self.current_session = 1
            self.total_sessions = total_sessions
            return

        if self.total_sessions != total_sessions:
            raise TotalSessionsMustMatchProjectError()

    def confirm_deposit(self):
        if self.status != AppointmentStatus.QUOTED:
            raise AppointmentMustBeInCorrectPreviousStatusError()
        if self.price is None:
            raise PriceMustBeDefinedError()

        self.deposit_confirmed_at = self._utc_now()
        self.status = AppointmentStatus.SCHEDULED
        self._touch()

    def complete(self, total_paid: Decimal) -> Optional[AppointmentCompleted]:
        if self.price is None:
            raise PriceMustBeDefinedError()

        if self.status != AppointmentStatus.SCHEDULED:
            raise AppointmentMustBeScheduledError()

        if total_paid < self.price:
            raise AppointmentWasNotFullyPaidError("please_check_payments_and_possible_refunds")

        self.status = AppointmentStatus.COMPLETED
        self._touch()
        if self.referral_code is not None:
            return AppointmentCompleted(
                appointment_id=self.id,
                referral_code=self.referral_code,
                client_info=self.client_info,
            )

        return None

    def mark_as_canceled(self, observations: str):
        self.status = AppointmentStatus.CANCELED
        self.add_observations(observations)

    def add_observations(self, new_observation: str):
        if self.observations:
            self.observations += f"\n{new_observation}"
        else:
            self.observations = new_observation
        self._touch()

    def create_appointment_request(
        self,
    ) -> CreateAppointmentEmailRequested:

        if self.client_info.email is not None:
            recipient = self.client_info.email
        elif self.client_info.vip_client_id is not None:
            recipient = self.client_info.vip_client_id
        else:
            raise AppointmentClientContactInfoCorruptedError()

        return CreateAppointmentEmailRequested(
            start_at=self.start_at,
            end_at=self.end_at,
            appointment_type=self.appointment_type,
            user_id=self.user_id,
            client_email_or_vip_id=recipient,
        )

    def notify_of_appointment_quoted(
        self,
    ) -> NotifyOfAppointmentQuoted:

        if self.client_info.email is not None:
            recipient = self.client_info.email
        elif self.client_info.vip_client_id is not None:
            recipient = self.client_info.vip_client_id
        else:
            raise AppointmentClientContactInfoCorruptedError()

        if self.price is None:
            raise PriceMustBeDefinedError()

        return NotifyOfAppointmentQuoted(
            appointment_type=self.appointment_type,
            client_email_or_vip_id=recipient,
            total_sessions=self.total_sessions,
            current_session=self.current_session,
            price=self.price,
        )

    def _touch(self):
        self.updated_at = self._utc_now()

    def _validate_state(self):
        if self.total_sessions is not None:
            self._validate_total_sessions_value(self.total_sessions)
        if self.current_session is not None:
            if self.total_sessions is None:
                raise TotalSessionsNumberMustBeDefineError()
            if self.current_session < 1:
                raise CurrentSessionMustBePositiveError()
            if self.current_session > self.total_sessions:
                raise CurrentSessionMustBeLessThanTotalError()

        if self.project_id is not None:
            if self.total_sessions is None or self.total_sessions < 2 or self.current_session is None:
                raise AppointmentProjectStateError()
        elif self.total_sessions is not None and self.total_sessions > 1:
            raise ForMultipleSessionsProjectIdMustBeDefinedError()
        if self.status == AppointmentStatus.REQUESTED:
            if self.price is not None:
                raise AppointmentStatusBreakingDomainRules("status_requested_does_not_suport_price")
            if self.deposit_confirmed_at is not None:
                raise AppointmentStatusBreakingDomainRules("status_requested_does_not_suport_deposit")

        elif self.status == AppointmentStatus.QUOTED:
            if self.price is None:
                raise AppointmentStatusBreakingDomainRules("status_quoted_must_have_price")
            if self.deposit_confirmed_at is not None:
                raise AppointmentStatusBreakingDomainRules("status_quoted_does_not_suport_deposit")

        elif self.status == AppointmentStatus.SCHEDULED:
            if self.price is None:
                raise AppointmentStatusBreakingDomainRules("status_scheduled_must_have_price")
            if self.deposit_confirmed_at is None:
                raise AppointmentStatusBreakingDomainRules("status_scheduled_must_have_deposit")

        if self.end_at <= self.start_at:
            raise AppointmentMustHaveRealisticTimeAndDateError()

    @staticmethod
    def _validate_total_sessions_value(total_sessions: int) -> None:
        if total_sessions < 1:
            raise TotalSessionsNumberMustBePositiveError()
        if total_sessions == 1:
            raise TotalSessionsMustBeAtLeastTwoError()

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)


"""
TODO — Etapas restantes do acompanhamento de projetos de múltiplas sessões.

Objetivo
--------
Permitir que vários Appointment representem sessões diferentes de uma mesma
tatuagem/projeto, sem criar uma nova entidade ou tabela para o projeto.

A solução será baseada em um `project_id` compartilhado entre todos os
appointments que pertencem ao mesmo projeto.

Exemplo:

    Appointment 1:
        project_id = UUID("abc...")
        current_session = 1
        total_sessions = 4

    Appointment 2:
        project_id = UUID("abc...")
        current_session = 2
        total_sessions = 4

    Appointment 3:
        project_id = UUID("abc...")
        current_session = 3
        total_sessions = 4

    Appointment 4:
        project_id = UUID("abc...")
        current_session = 4
        total_sessions = 4

Não criar uma entidade `TattooProject`, `SessionGroup` ou tabela separada
neste momento. O `project_id` será apenas um identificador compartilhado
diretamente pelos appointments.

A intenção futura é usar esse agrupamento principalmente para:

    1. Saber quais appointments pertencem ao mesmo projeto.
    2. Saber qual foi a última sessão concluída.
    3. Saber se o projeto já foi concluído.
    4. Saber se o cliente já possui uma próxima sessão agendada.
    5. Identificar projetos que ficaram parados por muito tempo.
    6. Futuramente enviar lembretes para clientes que começaram uma tatuagem
       de múltiplas sessões e não retornaram.

IMPORTANTE SOBRE `is_project_finished`
---------------------------------------
Não adicionar `is_project_finished` como campo persistido no Appointment.

Essa informação é derivada dos appointments do projeto.

Por exemplo:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 COMPLETED
    4/4 COMPLETED

significa que o projeto terminou.

Já:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 COMPLETED

significa que ainda não terminou.

Armazenar `is_project_finished` em cada Appointment criaria estado derivado
que poderia ficar inconsistente, principalmente se `total_sessions` fosse
alterado posteriormente.

A regra será:

    project_finished =
        última sessão concluída == total_sessions

O `project_id` é o dado persistido; o estado de conclusão será calculado.

--------------------------------------------------
1. CONSULTAS FUTURAS NO REPOSITORY
--------------------------------------------------

Também será necessário considerar métodos para buscar projetos que possuem
appointments incompletos.

Evitar carregar todos os appointments do banco para Python para depois
agrupar manualmente.

O banco deve fazer o máximo possível do agrupamento e filtragem.

A camada de repository deve fornecer dados próximos do que o caso de uso
realmente precisa.

--------------------------------------------------
2. CONSULTA PARA IDENTIFICAR PROJETOS
--------------------------------------------------

O conceito importante é:

    um projeto = todos os appointments com o mesmo project_id

Por exemplo:

    project_id ABC

        1/4 COMPLETED
        2/4 COMPLETED
        3/4 COMPLETED

Para determinar o estado atual do projeto, procurar a maior sessão relevante.

Porém, NÃO assumir simplesmente:

    MAX(current_session)

sem considerar o status do appointment.

Appointments CANCELLED, REQUESTED ou outros estados que não representam
sessões efetivamente realizadas/agendadas podem interferir no cálculo.

A lógica deverá distinguir pelo menos:

    sessões concluídas
    sessões futuras/agendadas
    appointments cancelados
    appointments que ainda não foram confirmados

--------------------------------------------------
3. DEFINIÇÃO DE "PROJETO FINALIZADO"
--------------------------------------------------

O projeto está finalizado quando a última sessão efetivamente concluída
atinge `total_sessions`.

Exemplo:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 COMPLETED
    4/4 COMPLETED

Resultado:

    project_finished = True

Não considerar uma sessão apenas REQUESTED ou QUOTED como concluída.

Também não considerar uma sessão SCHEDULED como concluída.

Exemplo:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 COMPLETED
    4/4 SCHEDULED

Resultado:

    project_finished = False

O projeto ainda está em andamento, embora a última sessão já esteja
agendada.

--------------------------------------------------
4. DEFINIÇÃO DE "PROJETO INCOMPLETO"
--------------------------------------------------

Um projeto é candidato a estar incompleto quando:

    última sessão concluída < total_sessions

Exemplo:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 COMPLETED

Resultado:

    current_session = 3
    total_sessions = 4
    project_finished = False

--------------------------------------------------
5. NÃO ENVIAR LEMBRETE SE JÁ EXISTIR PRÓXIMA SESSÃO
--------------------------------------------------

Este é um ponto importante.

Exemplo:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 COMPLETED
    4/4 SCHEDULED

O projeto ainda não está concluído, mas o cliente já tem a continuação
agendada.

Portanto:

    NÃO enviar lembrete.

A consulta deverá procurar appointments futuros/agendados do mesmo
`project_id` cuja sessão seja posterior à última sessão concluída.

Exemplo:

    última concluída = 3
    existe 4/4 SCHEDULED

Então:

    has_future_session = True

e o projeto não deve entrar na lista de lembretes.

--------------------------------------------------
6. CÁLCULO PARA O SCRIPT DE LEMBRETES
--------------------------------------------------

O script deverá executar aproximadamente a seguinte lógica:

    1. Encontrar projetos com múltiplas sessões.
    2. Agrupar appointments por `project_id`.
    3. Para cada projeto:
        a. encontrar a última sessão COMPLETED;
        b. descobrir current_session;
        c. descobrir total_sessions;
        d. verificar se current_session == total_sessions;
        e. se terminou, ignorar;
        f. procurar uma próxima sessão já agendada;
        g. se houver próxima sessão, ignorar;
        h. calcular quanto tempo passou desde a última sessão concluída;
        i. se ultrapassar o limite definido, considerar o cliente para
           lembrete.

Pseudocódigo:

    for project in projects:

        last_completed = find_last_completed_session(project)

        if last_completed is None:
            continue

        if last_completed.current_session >= last_completed.total_sessions:
            continue

        has_future_session = exists_future_scheduled_session(
            project_id=project.id,
            after_session=last_completed.current_session,
        )

        if has_future_session:
            continue

        elapsed = now - last_completed.end_at

        if elapsed >= REMINDER_THRESHOLD:
            notify_client(project)

--------------------------------------------------
7. QUAL DATA USAR NO CÁLCULO DO TEMPO?
--------------------------------------------------

Usar preferencialmente `end_at` da última sessão COMPLETED.

Não utilizar:

    created_at
    updated_at

porque essas datas não representam quando a sessão foi realizada.

Exemplo:

    sessão 3/4
    start_at = 2026-01-10 14:00
    end_at   = 2026-01-10 17:00

O cálculo deverá utilizar:

    now - end_at

Isso representa melhor o tempo desde que o cliente efetivamente realizou
a última sessão.

--------------------------------------------------
8. CASO DE SESSÃO FUTURA AGENDADA
--------------------------------------------------

Exemplo:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 SCHEDULED

A última sessão concluída é:

    2/4

Existe uma sessão futura:

    3/4 SCHEDULED

Logo:

    não enviar lembrete.

Também deve ser considerado um appointment futuro com sessão posterior
mesmo que não seja exatamente `current_session + 1`, caso o domínio permita
gaps.

Por exemplo:

    2/4 COMPLETED
    4/4 SCHEDULED

Nesse caso existe claramente uma sessão futura, portanto não enviar
lembrete automaticamente.

Porém, considerar se o domínio deverá proibir gaps entre sessões.

--------------------------------------------------
9. DECISÃO PENDENTE SOBRE CANCELAMENTOS E NUMERAÇÃO
--------------------------------------------------

Atualmente, a criação de uma nova sessão já garante que:

    new_current_session == last_session + 1

Ainda é preciso decidir se uma sessão CANCELLED consome sua numeração ou se
uma nova tentativa reutiliza o mesmo `current_session`. Essa decisão afeta a
criação e o cálculo de lembretes. Ao procurar se existe continuação agendada,
deve-se considerar qualquer sessão válida posterior:

    scheduled.current_session > last_completed.current_session

--------------------------------------------------
10. CANCELAMENTO DE SESSÕES
--------------------------------------------------

O cálculo deverá ignorar appointments CANCELLED como sessões concluídas.

Exemplo:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 CANCELED

Resultado:

    última sessão concluída = 2/4

Se posteriormente houver:

    3/4 SCHEDULED

então não enviar lembrete.

Se não houver nova sessão agendada e passar o limite de tempo, o projeto
poderá voltar a ser candidato ao lembrete.

Também pode haver várias tentativas de agendamento da mesma sessão:

    3/4 CANCELED
    3/4 CANCELED
    3/4 SCHEDULED

O script deverá considerar o SCHEDULED válido e ignorar os cancelados.

--------------------------------------------------
11. ALTERAÇÃO DE `total_sessions`
--------------------------------------------------

É possível que o número total de sessões seja alterado.

Exemplo:

    1/4
    2/4
    3/4

e posteriormente:

    total_sessions = 5

Nesse caso o projeto passa a ser:

    3/5

Não persistir `is_project_finished`, justamente para evitar inconsistência.

Se `total_sessions` for reduzido:

    1/5
    2/5
    3/5

para:

    total_sessions = 3

então a última sessão passa a representar:

    3/3

e o projeto pode ser considerado concluído.

Essa alteração deve ser protegida pelas regras de domínio para evitar
estados impossíveis.

--------------------------------------------------
12. TESTES FUTUROS DO REPOSITORY
--------------------------------------------------

Testar:

    - appointments normais com project_id NULL
    - vários projetos do mesmo cliente
    - appointments cancelados
    - appointments scheduled
    - appointments completed

Exemplo:

    cliente João:

        projeto ABC:
            1/4
            2/4

        projeto XYZ:
            1/3
            2/3

O repository deve ser capaz de tratar ABC e XYZ como projetos
completamente independentes.

--------------------------------------------------
13. TESTES DO SCRIPT DE LEMBRETES
--------------------------------------------------

Criar cenários explícitos para:

CASO 1 — Projeto concluído:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 COMPLETED
    4/4 COMPLETED

    => não lembrar


CASO 2 — Projeto incompleto:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 COMPLETED

    => candidato


CASO 3 — Próxima sessão agendada:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 COMPLETED
    4/4 SCHEDULED

    => não lembrar


CASO 4 — Sessão seguinte cancelada:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 CANCELED

    => projeto continua em 2/4


CASO 5 — Próxima sessão reagendada:

    1/4 COMPLETED
    2/4 COMPLETED
    3/4 CANCELED
    3/4 SCHEDULED

    => não lembrar


CASO 6 — Vários projetos do mesmo cliente:

    Projeto A:
        1/4 COMPLETED
        2/4 COMPLETED

    Projeto B:
        1/3 COMPLETED
        2/3 COMPLETED
        3/3 COMPLETED

    => A é incompleto
    => B é concluído


CASO 7 — Projeto parado há muito tempo:

    1/4 COMPLETED
    2/4 COMPLETED

    última sessão ocorreu há mais que REMINDER_THRESHOLD

    => lembrar


CASO 8 — Projeto parado, mas dentro do limite:

    1/4 COMPLETED
    2/4 COMPLETED

    última sessão ocorreu há menos que REMINDER_THRESHOLD

    => não lembrar


CASO 9 — Sessão futura posterior:

    1/4 COMPLETED
    2/4 COMPLETED
    4/4 SCHEDULED

    => não lembrar automaticamente, caso gaps sejam permitidos


CASO 10 — Projeto sem nenhuma sessão completed:

    1/4 REQUESTED

    => não considerar como projeto parado após uma sessão realizada.


--------------------------------------------------
14. POSSÍVEL IMPLEMENTAÇÃO FUTURA DO REMINDER JOB
--------------------------------------------------

O job não deve enviar diretamente o e-mail a partir do repository.

Responsabilidades:

    Repository:
        buscar os dados necessários.

    Application/use case:
        aplicar as regras de negócio:
            projeto terminou?
            há próxima sessão?
            passou o tempo limite?

    Event bus / handler:
        realizar o envio da notificação.

Fluxo desejado:

    Scheduled Job
        ↓
    Use Case
        ↓
    Repository
        ↓
    identifica projetos inativos
        ↓
    Use Case
        ↓
    evento de domínio/aplicação
        ↓
    Email Handler
        ↓
    cliente recebe lembrete

--------------------------------------------------
15. FUTURA PREVENÇÃO DE SPAM
--------------------------------------------------

Quando o sistema de lembretes for realmente implementado, considerar
também guardar informações sobre o último lembrete enviado.

Não implementar necessariamente agora.

Futuramente pode ser necessário algo como:

    last_project_reminder_sent_at

ou uma tabela/evento de notificações.

Isso será importante para evitar que um job executado semanalmente envie
um e-mail para o mesmo cliente toda semana.

Também considerar:

    - intervalo mínimo entre lembretes;
    - máximo de lembretes por projeto;
    - parar lembretes após o cliente retornar;
    - parar lembretes se o projeto for concluído;
    - respeitar opt-out de comunicações de marketing.

--------------------------------------------------
16. DECISÃO ARQUITETURAL
--------------------------------------------------

A solução escolhida deliberadamente NÃO cria:

    TattooProject
    SessionGroup
    Project table
    Project entity
    is_project_finished persistido

A solução inicial será:

    Appointment
        project_id: UUID | None
        current_session: int | None
        total_sessions: int | None

`project_id` identifica quais appointments pertencem ao mesmo projeto.

`current_session` identifica a posição daquela sessão dentro do projeto.

`total_sessions` informa quantas sessões são esperadas.

O estado "projeto concluído" será derivado dos appointments.

Essa abordagem mantém o domínio simples neste momento e ainda permite
implementar posteriormente:

    - acompanhamento de projetos;
    - detecção de projetos abandonados;
    - lembretes automáticos;
    - estatísticas de projetos;
    - análise de taxa de conclusão;
    - campanhas de retorno de clientes.

Se no futuro surgirem muitos atributos próprios do projeto (preço total,
descrição geral, data de início, data de conclusão, status do projeto,
lembretes, etc.), reavaliar a decisão e considerar transformar o projeto
em uma entidade própria.
"""

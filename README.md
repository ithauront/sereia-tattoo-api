# Sereia Tattoo API — Guia de Instalação e Execução

Este passo a passo cobre do zero: preparar o ambiente, configurar variáveis, instalar dependências, executar migrações do Alembic, popular seeds e subir o servidor.
Inclui dois caminhos para quem tem Python antigo (3.8/3.9): usando o uv (recomendado, sem mexer no sistema) ou atualizando o Python no sistema.

## Requisitos

Git

SQLite

Linux/Mac (testado no Ubuntu/Mint); no Windows, use WSL2

## Instalação

1. Clonar o projeto

```bash
git clone https://github.com/ithauront/sereia-tattoo-api.git
cd sereia-tattoo-api
```

2. Variáveis de ambiente

Crie um arquivo .env na raiz do projeto:

```bash
PROJECT_NAME="sereia_tattoo_api"
API="/api"
DATABASE_URL="sqlite:///./app.db"

# JWT
SECRET_KEY="sua_chave_secreta"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=1440
```

3. Escolha UMA forma de ter Python 3.11+
   Opção A — uv (recomendado; não precisa sudo nem alterar o sistema)

1) Instalar o uv (user-space):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# recarregar o shell para ter o uv no PATH
exec $SHELL
```

2. Criar um venv com Python 3.11 dentro do projeto:

```bash
# na raiz do projeto
rm -rf .venv
uv python install 3.11
uv venv --python 3.11 .venv
source .venv/bin/activate
python -V    # deve mostrar Python 3.11.x
```

3. Instalar dependencias:

```bash
uv pip install -U pip
uv pip install -r requirements.txt
```

Opção B — Atualizar o Python no sistema (se preferir)
**Atenção: em distros antigas (Ubuntu 20.04/Mint uma) o python3.11 nem sempre está disponível por APT. Se der erro, use a Opção A (uv).**
Com pyenv (recomendado para gerenciar versões):

```bash
curl https://pyenv.run | bash
# siga as instruções impressas para adicionar pyenv ao ~/.zshrc ou ~/.bashrc, depois:
exec $SHELL

pyenv install 3.11.13
pyenv local 3.11.13

python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

4. Banco de dados e migrações
   Subir banco de dados:

```bash
docker compose up -d
```

1. Criar/atualizar a base (Alembic):

```bash
# sempre pelo python do venv, para evitar pegar alembic global:
python -m alembic upgrade head
```

2. adicionar o seed de admins (apenas em ambiente dev):

```bash
python -m app.scripts.seed_admins_dev
```

5. Rodar o servidor

```bash
python -m uvicorn app.main:app --reload
```

A API deverá estar acessível em http://127.0.0.1:8000

Lembre de sempre rodar o projeto dentro de um ambiente virtual com o comando

```bash
source .venv/bin/activate
```

## Testes

O projeto possui testes de:

UseCases (login, refresh, verify)

JWT service

Fake repositories

SQLAlchemy repositories (testes reais com banco)

Para rodar:

```bash
pytest -q
```

## Rotas

O servidor tem rotas para criar validar e dar refresh em tokens (JWT)
Temos as seguintes rotas:
POST http://127.0.0.1:8000/api/auth/login
enviando no body um json com:
{
"username":"admin1",
"password":"admin1pass"
}
ou qualquer outro admin que você tenha criado no arquivo de seed admins
Voce vai ter como resposta o access_token, o refresh_token e o token_type

POST http://127.0.0.1:8000/api/auth/refresh
enviando um body json com:
{
"refresh_token":"cole aqui o refreshtoken recebido ao fazer o login"
}

GET http://127.0.0.1:8000/api/auth/verify
enviando no header um bearer token com o seu access token.

PATCH `/api/appointments/{appointment_id}/quote`

Rota utilizada para definir o preço de um agendamento.

O body deve ser enviado como JSON:

```json
{
  "price": "700,50"
}
```

O campo `price` aceita valores decimais usando **ponto ou vírgula como separador decimal**. O backend normaliza ambos os formatos para `Decimal`.

**Formatos aceitos**

```json
{ "price": "700.50" }
```

```json
{ "price": "700,50" }
```

Também são aceitos valores sem casas decimais:

```json
{ "price": "700" }
```

O valor será convertido e armazenado como `Decimal`.

**Formatos não aceitos**

O preço deve ser um número positivo, com **no máximo 2 casas decimais**.

Exemplos que retornam `422 Unprocessable Entity`:

```json
{ "price": "not-a-decimal" }
```

```json
{ "price": "700.501" }
```

```json
{ "price": "700,501" }
```

```json
{ "price": "4.700.50" }
```

```json
{ "price": "4,700,50" }
```

Também não é permitido omitir o campo:

```json
{}
```

Valores `0` ou negativos também são rejeitados:

```json
{ "price": "0" }
```

```json
{ "price": "-50" }
```

**Observação para o frontend**

O frontend pode enviar o preço utilizando `.` ou `,` como separador decimal. Por exemplo, tanto `"700.50"` quanto `"700,50"` serão interpretados como `700.50`.

O backend **não aceita separadores de milhares**. Portanto, valores como `"4.700,50"` ou `"4,700.50"` devem ser normalizados pelo frontend antes do envio.

## Pagamentos e caução

Um appointment pode possuir vários pagamentos e cada pagamento registra separadamente
o método utilizado, como PIX, dinheiro ou cartão.

Quando a caução for dividida entre vários métodos, o operador registra o primeiro
recebimento com o propósito `DEPOSIT`. Esse lançamento confirma a caução e dispara a
transição do appointment de `QUOTED` para `SCHEDULED`.

Os recebimentos seguintes são registrados com o propósito `APPOINTMENT`, mesmo que
tenham sido combinados com o cliente como parte do valor antecipado. Todos os pagamentos
com propósito `DEPOSIT` ou `APPOINTMENT` vinculados ao appointment compõem o total pago e
reduzem o saldo restante. Pagamentos com propósito `TIP` ou `OTHER` não quitam o preço do
appointment.

Essa convenção evita confirmar a mesma caução várias vezes e não exige agrupar pagamentos
feitos por métodos diferentes.

### Idempotência na criação de pagamentos

Toda solicitação de criação de pagamento deve incluir o campo
`idempotency_key`. O frontend deve gerar um UUID v4 novo quando o usuário iniciar
uma nova operação de pagamento:

```json
{
  "idempotency_key": "05df804e-223a-4f34-bc40-9e98a6809782"
}
```

Essa chave deve ser gerada apenas uma vez por operação e reutilizada sem
alteração em todas as tentativas causadas por timeout, falha de rede ou retry.
Um pagamento diferente deve sempre receber uma chave nova. O frontend não deve
gerar outra chave apenas porque não recebeu a resposta da primeira tentativa.

Internamente, a API usa `idempotency_key` como o `payment.id` definitivo. Por isso,
não existe um segundo identificador provisório, e a chave não deve ser reutilizada
para outro pagamento.

Quando uma chave já existe:

- se todos os dados do pagamento forem iguais, a API retorna o pagamento existente
  e não cria novos registros de pagamento, crédito ou auditoria;
- se algum dado for diferente, a API rejeita a solicitação como conflito de
  idempotência.

O UUID pode ser gerado no navegador com `crypto.randomUUID()`:

```javascript
const idempotencyKey = crypto.randomUUID();
```

O valor deve ser enviado no campo JSON `idempotency_key`. Ele não deve ser enviado
como `payment_id`, `temporary_id` ou `frontend_id`.

### Arredondamento dos créditos de cliente

Os créditos são unidades inteiras e `1 crédito` equivale a `R$ 1,00`. Como os
pagamentos aceitam centavos, a criação e o consumo de créditos seguem regras de
arredondamento diferentes e intencionais.

Na geração de créditos por indicação, o sistema calcula a porcentagem aplicável
sobre os pagamentos elegíveis do appointment e arredonda o resultado para cima.
Por exemplo, `10,01` créditos calculados geram `11` créditos. A diferença é sempre
inferior a um crédito por appointment que gera a bonificação.

No pagamento com créditos, o sistema arredonda o valor para baixo. Por exemplo, um
pagamento de `R$ 10,99` consome `10` créditos. A diferença também é sempre inferior
a um crédito por pagamento.

Consequentemente, uma geração seguida de um consumo pode produzir uma vantagem
total inferior a dois créditos. Esse limite é por par de operações, não um limite
global: as diferenças podem se acumular quando existem vários appointments ou
pagamentos.

Pagamentos com créditos abaixo de `R$ 1,00` resultariam em consumo de zero créditos
e não são aceitos pelo ledger atual. Essa regra deve ser reconsiderada caso valores
fracionários passem a ser frequentes no negócio.

## LOGOUT

Estamos usando um sistema de tokens para autentificação totalmente stateless com versionamento de access e refresh token. o tradeoff disso é que no momento de logout o access token com a versão antiga ainda fica valido até sua expiração (tempo curto, porem existente). Para mitigar isso na experiencia para usuario é essencial que o frontend remova os cookies de access e refresh token no momento de logout confirmado.

## Validações

Fazemos validações de username e password no backend. Para estarem nos conformes essas são as regras:
USERNAME:

- Não pode conter espaços
- Deve ter entre 3 e 30 caracteres
- Deve conter letras
- Pode conter numeros, ponto, underline e hifen seguindo esse regex
  ```python
   USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9._-]+$")
  ```

PASSWORD:

- Não pode conter espaços
- Deve ter ao menos 8 caracteres
- Deve ter letras maiusculas
- Deve ter letras minusculas
- Deve ter numero
- Pode ter mas não é obrigatorio de ter caracteres especiais

## FRONTEND:

### Atualização de e-mail de user

Não há um mecanismo de "change pending" para alterações de e-mail. Portanto, recomenda-se que o frontend faça uma validação dupla do input do usuário antes de enviar a atualização para o backend.

### Criação de cliente vip

No fluxo de criação de um cliente VIP, o frontend precisa preencher um formulário e obter clientcodes antes de criar o usuário. O processo é o seguinte:

1. O frontend faz uma requisição POST para /users/vip-client/generate-client-codes com um token de admin autenticado.

2. O backend retorna até 3 clientcodes disponíveis.

3 O frontend escolhe 1 clientcode e, no momento de criar o usuário, envia esse código junto com as demais informações do cliente.

**Detalhes importantes sobre os clientcodes:**

- Cada clientcode será gerado com: name + color + número (opcional).
- Color e número são gerenciados pelo backend.
- O name deve ser enviado pelo frontend. A convenção do sistema recomenda (inicialmente) enviar o firstname do cliente.
- Caso o backend retorne o erro 409: "please_try_creating_client_code_with_last_name", o frontend deve tentar enviar o lastname.
- A decisão de automatizar o envio do firstname e, no retry enviar o lastname, ou de deixar o usuário escolher, fica a cargo do frontend. O importante é sugerir enviar o firstname inicialmente e o lastname apenas em caso de erro.

### Fluxo de Pagamento de Appointment (VIP Context)

Visão geral:
O fechamento de um appointment exige que todos os pagamentos sejam processados antes de marcá-lo como done.
O sistema suporta pagamentos via múltiplos métodos, incluindo créditos de clientes VIP.

Contexto de VIP Client (temporário):
Ao iniciar o fluxo de pagamento de um appointment, o frontend pode opcionalmente buscar um VIP Client.

Quando encontrado, o frontend deve:

- Exibir o saldo de créditos do cliente VIP
- Manter esse cliente ativo apenas durante o fluxo do appointment atual
- Exibir um cabeçalho persistente com:
- nome do cliente
- saldo de créditos
- identificação do appointment ativo

Esse contexto NÃO representa autenticação, apenas estado de UI.

Fluxo recomendado:

1. Seleção do appointment

O usuário seleciona um appointment na interface.

2. Resolução de cliente VIP (opcional)

O frontend pode buscar um VIP client e anexá-lo ao contexto do appointment.

3. Exibição do contexto de pagamento

O sistema deve exibir:

- valor total do appointment
- saldo de créditos (se existir VIP client)
- opções de pagamento:
  dinheiro/cartão/etc
- créditos do cliente VIP
- valor ja pago

4 Pagamento (obrigatório antes de finalizar)

O frontend deve realizar chamadas para a api realizando pagamentos. multiplos pagamentos com diferentes typos (credito, dinheiro, cartão) são possiveis. e o saldo pago vai se somando e mostrando o quanto resta pagar.

5. Finalização do appointment

Somente após pagamentos concluídos:

o frontend pode chamar mark appointment as done

6. Limpeza de contexto

Após finalização:

remover VIP client da tela
resetar estado de pagamento (os pagamentos reais foram persistidos no B.E)
voltar para lista de appointments ou agenda ou pagina inicial

## AUDIT

Os logs de auditoria não fazem parte do domínio neste projeto.

Isso porque, no cenário atual, eles:

- não influenciam regras de negócio
- não são utilizados para tomada de decisão dentro do sistema
- servem apenas para rastreamento, debugging e observabilidade

Por esse motivo, optamos por tratá-los como uma preocupação de infraestrutura.

Os logs de auditoria são implementados com:

- Model (SQLAlchemy) → persistência no banco de dados
- Repository (infraestrutura) → responsável por salvar e consultar logs
- DTO (AuditLogEntry) → estrutura tipada utilizada pela camada de aplicação
- Integração com Unit of Work → garante consistência transacional

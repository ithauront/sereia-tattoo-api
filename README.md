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

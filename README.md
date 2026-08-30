# O Grimório — Workshop de Backend (Fábrica de Software 26.2)

API REST em Django para gerenciar personagens de RPG e seus feitiços. Ao adicionar uma magia, o backend busca os atributos oficiais na [D&D 5e API](https://www.dnd5eapi.co/) e persiste uma cópia local no banco (cache), associada ao personagem por chave estrangeira — incluindo detalhes de conjuração como tempo, alcance, componentes, duração, dano e teste de resistência.


## Stack

- **Django** + **Django REST Framework** — API e ORM
- **PostgreSQL** — banco de dados externo
- **djangorestframework-simplejwt** — autenticação por token JWT
- **drf-spectacular** — documentação OpenAPI/Swagger
- **django-environ** — variáveis de ambiente fora do código-fonte
- **django-cors-headers** — CORS para clientes externos
- **Docker Compose** — orquestração do banco de dados e da aplicação

---

## Antes de começar

Você vai precisar ter instalado na sua máquina:

| Ferramenta | Para quê | Link |
|---|---|---|
| **Git** | Baixar o código | [git-scm.com](https://git-scm.com/downloads) |
| **Python 3.12+** | Rodar o Django | [python.org/downloads](https://www.python.org/downloads/) |
| **Docker Desktop** | Rodar o banco (e opcionalmente a aplicação) | [docker.com/get-started](https://www.docker.com/products/docker-desktop/) |

> ⚠️ **O erro mais comum ao rodar este projeto é esquecer de abrir o Docker Desktop antes.**
> No Windows/Mac, o Docker Desktop precisa estar **aberto e rodando** (ícone da baleia na bandeja do sistema) antes de qualquer comando `docker-compose`. Se ele não estiver aberto, todo comando `docker-compose up` vai falhar silenciosamente ou travar.

---

## Como rodar localmente — passo a passo

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd wsBackendFabricaDeSoftware26.2
```

### 2. Configure as variáveis de ambiente

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Abra o `.env` criado e confira os valores (os padrões já funcionam para desenvolvimento local, não precisa mudar nada de cara). Esse arquivo nunca deve ser commitado — ele já está no `.gitignore`.

### 3. Suba o Docker Desktop

Abra o aplicativo **Docker Desktop** e espere o ícone da baleia ficar estável (não "carregando"). Sem isso, o próximo passo falha.

### 4. Suba o banco de dados (e a aplicação, se preferir tudo via Docker)

Você tem duas formas de rodar o projeto a partir daqui — escolha uma:

#### Opção A — Tudo via Docker (mais simples, recomendado)

```bash
docker-compose up -d
```

Isso sobe o PostgreSQL **e** a aplicação Django juntos; o serviço `web` só inicia depois que o banco reporta status saudável (healthcheck), então não precisa se preocupar com ordem de inicialização.

Confira se os dois containers subiram corretamente:

```bash
docker ps
```

Você deve ver dois containers rodando: `dnd_postgres` e `dnd_web`, ambos com status `Up`.

Aplique as migrações (cria as tabelas no banco):

```bash
docker-compose exec web python manage.py migrate
```

Crie um superusuário, se quiser acessar o `/admin/` do Django (opcional):

```bash
docker-compose exec web python manage.py createsuperuser
```

A aplicação já estará no ar em `http://localhost:8000/`.

#### Opção B — Só o banco via Docker, Django rodando direto na sua máquina

Útil se você quiser usar o autoreload do `runserver` sem depender de volumes do Docker.

```bash
docker-compose up -d db
```

Confirme que o banco está saudável:

```bash
docker ps
```

Você deve ver `dnd_postgres` com status `Up (healthy)`.

Crie e ative um ambiente virtual Python:

```bash
python -m venv venv
source venv/bin/activate       # Windows (PowerShell): venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

No `.env`, ajuste `DB_HOST=localhost` (o Docker Compose usa `DB_HOST=db`, que só funciona *entre containers*; rodando o Django fora do Docker, ele precisa falar com `localhost`).

Aplique as migrações e suba o servidor:

```bash
python manage.py migrate
python manage.py runserver
```

A aplicação estará em `http://localhost:8000/`.

### 5. Acesse a aplicação

- **Página funcional (SPA):** [http://localhost:8000/grimorio/](http://localhost:8000/grimorio/) — cadastre uma conta, faça login, crie um personagem e adicione magias (em inglês, ex: `fireball`, `cure wounds`).
- **Documentação Swagger:** [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/) — para testar a API diretamente ou entender o contrato de cada endpoint.
- **Admin do Django:** [http://localhost:8000/admin/](http://localhost:8000/admin/) — requer o superusuário criado no passo anterior.

---

## Problemas comuns (troubleshooting)

**`psycopg2.OperationalError: connection to server ... failed: Connection refused`**
O Postgres não está rodando. Confirme com `docker ps` — se `dnd_postgres` não aparecer, o Docker Desktop provavelmente não estava aberto quando você rodou `docker-compose up`, ou o container caiu. Rode `docker-compose up -d` de novo e depois `docker ps` pra confirmar.

**`docker-compose up` não mostra nenhum container em `docker ps`**
Rode `docker-compose up` (sem `-d`) para ver o log de erro na tela em tempo real. As causas mais comuns são porta já em uso (veja abaixo) ou variável de ambiente faltando no `.env`.

**Porta já em uso (`bind: address already in use`)**
Alguma coisa na sua máquina já está usando a porta 5433 (Postgres) ou 8000 (Django). Descubra o que está usando a porta ou mude o mapeamento no `docker-compose.yml` (ex: `"5434:5432"`) e ajuste `DB_PORT` no `.env` de acordo.

**A página `/grimorio/` abre em branco ou dá erro 404**
Confirme que está acessando exatamente `http://localhost:8000/grimorio/` (com a barra no final) e que o servidor Django está de fato rodando (veja o terminal ou `docker ps`).

**Adicionei uma magia e deu "Magia não encontrada"**
O nome precisa ser digitado **em inglês**, do jeito que aparece nos livros oficiais em inglês (ex: `fireball`, `magic missile`, `cure wounds`) — a D&D 5e API não tem os nomes traduzidos.

**Alterei um model e a migração não aparece**
Depois de mudar `core/models.py`, gere a migração antes de aplicar:

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

(ou sem Docker: `python manage.py makemigrations && python manage.py migrate`)

---

## Endpoints principais

Todas as rotas de `/api/`, exceto as de autenticação, exigem token JWT no header `Authorization: Bearer <token>`.

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/auth/register/` | Cria uma nova conta (público, sem token) |
| POST | `/api/auth/token/` | Obtém o par de tokens JWT (access/refresh) |
| POST | `/api/auth/token/refresh/` | Renova o access token |
| GET | `/api/personagens/` | Lista os personagens do usuário autenticado |
| POST | `/api/personagens/` | Cria um personagem |
| GET | `/api/personagens/{id}/` | Detalha um personagem |
| PUT/PATCH | `/api/personagens/{id}/` | Atualiza um personagem |
| DELETE | `/api/personagens/{id}/` | Remove um personagem |
| GET | `/api/magias/` | Lista as magias do usuário autenticado |
| POST | `/api/magias/` | Busca a magia na D&D 5e API pelo slug e persiste |
| DELETE | `/api/magias/{id}/` | Remove uma magia do grimório |
| GET | `/grimorio/` | Página funcional (SPA autenticada via JWT) |
| GET | `/api/docs/` | Documentação Swagger/OpenAPI |

### Exemplo: criar uma conta e autenticar

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "elandril", "password": "SenhaForte123!"}'

curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "elandril", "password": "SenhaForte123!"}'
```

### Exemplo: criar um personagem

```bash
curl -X POST http://localhost:8000/api/personagens/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"nome": "Elandril", "classe": "Mago", "nivel": 7}'
```

### Exemplo: adicionar uma magia

O campo `fonte_api` é o **slug** da magia na D&D 5e API (ex: `fireball`, `magic-missile`), não o nome livre.

```bash
curl -X POST http://localhost:8000/api/magias/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"fonte_api": "fireball", "personagem": 1}'
```

A resposta traz, além dos dados básicos, os detalhes de conjuração retornados pela API externa (quando a magia os possui): `tempo_conjuracao`, `alcance`, `componentes`, `material`, `duracao`, `ritual`, `concentracao`, `dano`, `cd` (teste de resistência) e `area_efeito`. Campos que não se aplicam à magia vêm como `null`. Veja um exemplo completo de resposta em `/api/docs/`.

## Rodando os testes

```bash
pytest
```

## Estrutura do projeto

```
wsBackendFabricaDeSoftware26.2/
├── core/                   # app único: models, views, serializers, services, urls
│   ├── services.py         # integração com a D&D 5e API
│   ├── tests/              # testes (services, views, registro)
│   └── templates/core/     # página funcional (SPA HTML/CSS/JS)
├── project/                # settings.py, urls raiz, wsgi/asgi
├── docker-compose.yml      # orquestra banco de dados + aplicação
├── Dockerfile              # imagem da aplicação Django
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Variáveis de ambiente

Veja `.env.example` para a lista completa de variáveis esperadas (banco de dados e `SECRET_KEY`). O arquivo `.env` real nunca é commitado.

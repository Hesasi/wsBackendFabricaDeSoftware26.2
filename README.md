# O Grimório — Workshop de Backend (Fábrica de Software 26.2)

API REST em Django para gerenciar personagens de RPG e seus feitiços. Ao adicionar uma magia, o backend busca os atributos oficiais na [D&D 5e API](https://www.dnd5eapi.co/) e persiste uma cópia local no banco (cache), associada ao personagem por chave estrangeira.

Arquitetura completa e decisões de design em `ADR-002-Grimorio.pdf` (mantido separadamente deste repositório).

## Stack

- **Django** + **Django REST Framework** — API e ORM
- **PostgreSQL** — banco de dados externo
- **djangorestframework-simplejwt** — autenticação por token JWT
- **drf-spectacular** — documentação OpenAPI/Swagger
- **django-environ** — variáveis de ambiente fora do código-fonte
- **django-cors-headers** — CORS para clientes externos
- **Docker Compose** — orquestração do banco de dados e da aplicação

## Pré-requisitos

- Python 3.12+
- Docker e Docker Compose

## Como rodar localmente

**1. Clone o repositório e crie o ambiente virtual**

```bash
git clone <url-do-repositorio>
cd wsBackendFabricaDeSoftware26.2
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

**2. Instale as dependências**

```bash
pip install -r requirements.txt
```

**3. Configure as variáveis de ambiente**

Copie o arquivo de exemplo e ajuste os valores se necessário:

```bash
cp .env.example .env
```

**4. Suba a aplicação com Docker Compose**

```bash
docker-compose up -d
```

Isso sobe o banco PostgreSQL e a aplicação Django juntos; o serviço `web` só inicia depois que o banco reporta status saudável (healthcheck).

**5. Aplique as migrações**

```bash
docker-compose exec web python manage.py migrate
```

**6. Crie um superusuário (opcional, para acessar o /admin/)**

```bash
docker-compose exec web python manage.py createsuperuser
```

A API estará disponível em `http://localhost:8000/`.

### Rodando sem Docker (alternativa)

```bash
python manage.py migrate
python manage.py runserver
```

Nesse caso, ajuste `DB_HOST=localhost` no `.env` (o Docker Compose usa `DB_HOST=db`).

## Endpoints principais

Todas as rotas de `/api/`, exceto a de autenticação, exigem token JWT no header `Authorization: Bearer <token>`.

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

## Rodando os testes

```bash
pytest
```

## Estrutura do projeto

```
wsBackendFabricaDeSoftware26.2/
├── core/                   # app único: models, views, serializers, services, urls
│   ├── services.py         # integração com a D&D 5e API
│   ├── tests/              # testes (services, views)
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

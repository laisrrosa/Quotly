# Quotly — Plataforma de Monitoramento e Análise de Ações

Projeto Final da disciplina **Laboratório de Programação II**.

O **Quotly** é uma plataforma web que integra duas APIs independentes (**Python/FastAPI** e **Java/Spring Boot**) consumidas por um **Front-end** para consulta de cotações, gerenciamento de alertas de preço e simulações/análises financeiras.

---

## 👥 Integrantes do Grupo
- **Integrante 1 (Back-end Core, Banco de Dados & API Java):** Edinho
- **Integrante 2 (Worker de Cotações & Notificações por E-mail):** *[Preencher nome]*
- **Integrante 3 (Front-end Web):** *[Preencher nome]*

---

## 🛠️ Tecnologias Utilizadas
- **API Python (`api-python/`):** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy, SQLite, Pydantic, Passlib (Bcrypt), Python-Jose (JWT).
- **API Java (`api-java/`):** Java 21, Spring Boot 3.4, Gradle.
- **Front-end (`frontend/`):** JavaScript / HTML / CSS (React + Vite).

---

## 📁 Estrutura do Repositório

```text
Quotly/
├── api-python/    # API REST em Python (FastAPI) - Porta 8000
├── api-java/      # API REST em Java (Spring Boot) - Porta 8085
├── frontend/      # Interface Web (a ser integrada)
└── README.md
```

---

## 🚀 Passo a Passo para Executar Localmente

### 1. API Python (`api-python/` — Porta `8000`)

```bash
cd api-python

# Criar e ativar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

Crie um arquivo `.env` dentro de `api-python/` com base nas variáveis abaixo:

```ini
SECRET_KEY="sua_chave_secreta_aqui"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL="sqlite:///./quotly.db"
PROJECT_NAME="Quotly API"
```

Crie as tabelas iniciais do banco e suba o servidor:

```bash
python -c "from app.database.session import engine, Base; from app.models import User, Alert, StockQuote; Base.metadata.create_all(bind=engine)"
python -m uvicorn app.main:app --reload --port 8000
```

- Documentação interativa (Swagger UI): `http://localhost:8000/docs`

---

### 2. API Java (`api-java/` — Porta `8085`)

Pré-requisito: **Java 21** instalado.

```bash
cd api-java
./gradlew bootRun
```

- Serviço disponível em: `http://localhost:8085`

---

## 📡 Lista de Endpoints

### API Python (`http://localhost:8000`)
| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| `GET` | `/` | Status da API Python |
| `POST` | `/api/auth/register` | Cadastro de novo usuário |
| `POST` | `/api/auth/login` | Autenticação e geração de token JWT |
| `GET` | `/api/auth/me` | Dados do usuário autenticado |
| `POST` | `/api/alerts/` | Criação de alerta de preço (autenticado) |
| `GET` | `/api/alerts/` | Listagem de alertas do usuário autenticado |
| `PATCH` | `/api/alerts/{alert_id}` | Atualização de alerta existente |
| `DELETE` | `/api/alerts/{alert_id}` | Remoção de alerta |
| `POST` | `/api/stocks/` | Registro de cotação no histórico |
| `GET` | `/api/stocks/{ticker}` | Cotação mais recente de um ativo |
| `GET` | `/api/stocks/{ticker}/history` | Histórico de cotações para gráficos |

### API Java (`http://localhost:8085`)
| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| `GET` | `/api/analytics/simulate` | Simulação de investimento com juros compostos (`ticker`, `initialAmount`, `monthlyContribution`, `months`, `annualRatePercent`) |
| `GET` | `/api/analytics/variation` | Análise de variação absoluta, percentual, tendência (`UP`/`DOWN`/`NEUTRAL`) e distância até preço-alvo (`ticker`, `currentPrice`, `previousClose`, `targetPrice` opcional) |

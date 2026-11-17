# Quotly — Plataforma de Monitoramento e Análise de Ações

Projeto final da disciplina **Laboratório de Programação II**.

O **Quotly** é uma plataforma web para consultar cotações de ações, criar alertas de preço (com aviso por e-mail) e fazer simulações financeiras. Ele é formado por duas APIs independentes, uma em **Python (FastAPI)** e outra em **Java (Spring Boot)**, consumidas por um **front-end em React**.

## Visão geral

| Parte | Pasta | Tecnologia | Endereço |
|---|---|---|---|
| API Python | `api-python/` | FastAPI, SQLAlchemy, SQLite, JWT | http://localhost:8000 |
| API Java | `api-java/` | Java 21, Spring Boot 3.4, Gradle | http://localhost:8085 |
| Front-end | `frontend/` | React, Vite, Tailwind CSS | http://localhost:5173 |
| Worker de alertas (opcional) | `api-python/app/workers/` | APScheduler | roda em segundo plano |

- A **API Python** cuida de cadastro e login, alertas de preço e cotações (buscadas na brapi e no Yahoo Finance).
- A **API Java** faz os cálculos de simulação de investimento e de variação de preço.
- O **worker** verifica os alertas a cada 5 minutos e envia o e-mail quando o preço atinge o alvo.

---

## Como executar

### Pré-requisitos

| Programa | Versão | Para quê |
|---|---|---|
| Python | 3.10 ou superior | API Python e worker |
| JDK (Java) | **21** (exatamente) | API Java |
| Node.js | 20.19 ou superior (ou 22.12+) | Front-end |
| Git | qualquer | baixar o projeto |

É preciso ter acesso à internet: a primeira execução baixa as dependências, e as cotações vêm de serviços externos.

```bash
git clone https://github.com/laisrrosa/Quotly.git
cd Quotly
```

Cada parte roda em um terminal próprio. Abra **três terminais** na pasta `Quotly` e siga os passos abaixo.

### Terminal 1 — API Python (porta 8000)

**Windows (PowerShell):**

```powershell
cd api-python
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-worker.txt
copy .env.example .env
copy .env.worker.example .env.worker
python -c "from app.database.session import engine, Base; from app.models import User, Alert, StockQuote; Base.metadata.create_all(bind=engine)"
python -m uvicorn app.main:app --port 8000
```

**Linux / macOS:**

```bash
cd api-python
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-worker.txt
cp .env.example .env
cp .env.worker.example .env.worker
python -c "from app.database.session import engine, Base; from app.models import User, Alert, StockQuote; Base.metadata.create_all(bind=engine)"
python -m uvicorn app.main:app --port 8000
```

O que esses comandos fazem, na ordem: criam o ambiente virtual, instalam as dependências (os **dois** arquivos de requisitos são necessários), criam os arquivos de configuração, criam as tabelas do banco SQLite (`quotly.db`) e sobem o servidor.

Pronto quando aparecer `Uvicorn running on http://127.0.0.1:8000`. A documentação interativa (Swagger) fica em http://localhost:8000/docs.

### Terminal 2 — API Java (porta 8085)

**Windows (PowerShell):**

```powershell
cd api-java
.\gradlew.bat bootRun
```

**Linux / macOS:**

```bash
cd api-java
./gradlew bootRun
```

A primeira execução demora alguns minutos, porque baixa o Gradle e as dependências. Pronto quando aparecer `Started AnalyticsApplication`; a barra de progresso fica parada em torno de 80%, o que é normal enquanto o servidor está no ar.

### Terminal 3 — Front-end (porta 5173)

Antes de subir, abra o arquivo `frontend/.env` e troque a última linha para usar as APIs reais:

```ini
VITE_USE_MOCK=false
```

Depois, no Windows, Linux ou macOS:

```bash
cd frontend
npm install
npm run dev
```

Abra **http://localhost:5173** no navegador.

> Com `VITE_USE_MOCK=true` (valor que vem no repositório) o front-end roda em **modo demonstração**, com dados simulados e sem precisar de nenhuma das APIs. Uma faixa amarela no topo da página indica esse modo.

### Terminal 4 (opcional) — Worker de alertas

Só é necessário para os alertas dispararem e o e-mail ser enviado. Com o ambiente virtual da API Python ativado:

```bash
cd api-python
python -m app.workers          # verifica os alertas a cada 5 minutos
python -m app.workers --once   # ou: faz uma única verificação e encerra
```

Por padrão o e-mail **não é enviado de verdade**: o conteúdo aparece no próprio terminal do worker (`EMAIL_BACKEND=console`). Para enviar e-mails reais, veja "Configurações opcionais".

---

## Roteiro rápido de teste

1. Em http://localhost:5173, clique em **Cadastre-se** e crie uma conta (a senha precisa ter 8 caracteres ou mais).
2. Em **Cotações**, comece a digitar um código (por exemplo `PETR`) e escolha uma sugestão. Aparecem o card com o preço e o gráfico de histórico; o preço se atualiza sozinho a cada minuto.
3. No card, clique em **☆ Salvar** e depois abra a aba **Salvos** para ver a lista de acesso rápido.
4. No card, clique em **🔔 Criar alerta**, escolha a condição e o preço-alvo. O alerta aparece em **Meus alertas**, onde pode ser editado, pausado ou excluído.
5. Em **Análises**, use **Usar cotação atual** e **Analisar** para a análise de variação, e **Simular** para a simulação de investimento. Essas duas funções são calculadas pela **API Java**.
6. Para ver um alerta disparar: crie um alerta "Subir acima de" com alvo **abaixo** do preço atual e rode `python -m app.workers --once` no Terminal 4. O alerta passa para "Disparado" e o e-mail aparece no terminal.

---

## Configurações opcionais

Ficam em `api-python/.env.worker`. Depois de alterar, reinicie a API Python e o worker.

| Variável | Para quê |
|---|---|
| `BRAPI_TOKEN` | Token gratuito da brapi (https://brapi.dev/dashboard). Sem ele, a brapi só responde PETR4, VALE3, MGLU3 e ITUB4; os demais ativos são buscados no Yahoo Finance. |
| `EMAIL_BACKEND=smtp` + `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Envia os e-mails de alerta de verdade (por exemplo, com uma caixa de testes do Mailtrap ou uma senha de app do Gmail). |
| `ALERT_CHECK_INTERVAL_MINUTES` | Intervalo de verificação dos alertas (padrão: 5 minutos). |

Mais detalhes sobre o worker em [`api-python/README_WORKER.md`](api-python/README_WORKER.md) e sobre o front-end em [`frontend/README.md`](frontend/README.md).

## Testes automatizados

A API Python tem 83 testes (cotações, worker, e-mail e integração com as rotas). Com o ambiente virtual ativado:

```bash
cd api-python
python -m pytest
```

---

## Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | O comando foi executado fora de `api-python/`. Entre na pasta antes. |
| `Activate.ps1` bloqueado no PowerShell | Rode `Set-ExecutionPolicy -Scope Process RemoteSigned` no mesmo terminal e tente de novo. |
| API Python não sobe e cita `SECRET_KEY` | Falta o arquivo `api-python/.env`. Copie o `.env.example`. |
| API Python não sobe e cita `httpx` ou `yfinance` | Falta instalar o `requirements-worker.txt`. |
| Gradle: `Cannot find a Java installation ... languageVersion=21` | O JDK 21 não está instalado. Instale (por exemplo, `winget install EclipseAdoptium.Temurin.21.JDK` no Windows), abra um terminal novo e rode `gradlew --stop` antes de tentar de novo. |
| Site com faixa amarela "Modo demonstração" | `frontend/.env` está com `VITE_USE_MOCK=true`. Troque para `false` e reinicie o `npm run dev`. |
| "Não foi possível conectar ao servidor" no login | A API Python não está rodando na porta 8000. |
| Tela Análises diz que não conectou | A API Java não está rodando na porta 8085. |
| "Serviço de cotações indisponível" | Sem internet, ou os serviços externos de cotação estão fora do ar. Tente de novo em instantes. |

---

## Endpoints

### API Python (`http://localhost:8000`)

As rotas marcadas com 🔒 exigem o cabeçalho `Authorization: Bearer <token>`.

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/` | Status da API |
| `POST` | `/api/auth/register` | Cadastro de usuário |
| `POST` | `/api/auth/login` | Login (formulário `username` + `password`); devolve o token JWT |
| `GET` | `/api/auth/me` 🔒 | Dados do usuário logado |
| `POST` | `/api/alerts/` 🔒 | Cria um alerta de preço |
| `GET` | `/api/alerts/` 🔒 | Lista os alertas do usuário |
| `PATCH` | `/api/alerts/{alert_id}` 🔒 | Atualiza um alerta |
| `DELETE` | `/api/alerts/{alert_id}` 🔒 | Remove um alerta |
| `GET` | `/api/quotes/{ticker}` 🔒 | Cotação atual de qualquer ativo, direto do mercado |
| `GET` | `/api/quotes/{ticker}/history` 🔒 | Histórico diário (`range=7d\|1mo\|6mo\|1y`) |
| `POST` | `/api/stocks/` | Registra uma cotação no banco (usado pelo worker) |
| `GET` | `/api/stocks/{ticker}` | Última cotação gravada no banco |
| `GET` | `/api/stocks/{ticker}/history` | Histórico das cotações gravadas no banco |

### API Java (`http://localhost:8085`)

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/analytics/simulate` | Simulação de investimento com juros compostos (`ticker`, `initialAmount`, `monthlyContribution`, `months`, `annualRatePercent`) |
| `GET` | `/api/analytics/variation` | Variação absoluta e percentual, tendência (`UP`/`DOWN`/`NEUTRAL`) e distância até o preço-alvo (`ticker`, `currentPrice`, `previousClose`, `targetPrice` opcional) |

## Estrutura do repositório

```text
Quotly/
├── api-python/          # API REST em Python (FastAPI)
│   ├── app/routes/      #   rotas: auth, alerts, quotes, stocks
│   ├── app/services/    #   cotações (brapi / Yahoo) e e-mail
│   ├── app/workers/     #   worker de alertas
│   └── tests/           #   testes automatizados (pytest)
├── api-java/            # API REST em Java (Spring Boot)
├── frontend/            # Interface web (React + Vite)
├── API_CONTRACT.md      # proposta inicial de contrato entre front-end e back-end
└── README.md
```

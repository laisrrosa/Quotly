# Quotly: cotações, worker de alertas e e-mails (Integrante 2)

Este módulo roda **dentro do back-end** (`backend/`) e usa os mesmos modelos e
o mesmo banco (`quotly.db`) do Integrante 1.

| Pasta / arquivo | O que faz |
|---|---|
| `app/services/market_data.py` | `get_current_quote` e `get_historical_quotes` (brapi + Yahoo, cache, fallback) |
| `app/services/email_service.py` | e-mail de alerta (SMTP ou só log) |
| `app/templates/email/` | templates HTML e texto puro |
| `app/workers/` | monitor de alertas, repositório SQLAlchemy, agendador |
| `app/routes/quotes.py` | rotas `/api/quotes/...` do contrato do front-end |
| `app/core/worker_config.py`, `logging_config.py` | configuração e logs do módulo |
| `scripts/` | testes manuais pelo terminal |
| `tests/` | 83 testes (`pytest`) |
| `requirements-worker.txt` | dependências extras do módulo |
| `.env.worker.example` | variáveis do módulo (copiar para `.env.worker`) |

## Instalação (dentro de `backend/`)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1          # Linux/Mac: source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-worker.txt
copy .env.worker.example .env.worker    # Linux/Mac: cp
python -m pytest
```

Este módulo **não altera nenhum arquivo do back-end nem do front-end**: só
adiciona arquivos novos. Por isso:

- as dependências extras ficam em `requirements-worker.txt`;
- as variáveis ficam em `.env.worker`, e não no `.env` do back-end (a classe
  `Settings` do back-end recusa variáveis que ela não conhece, e a API deixaria
  de subir).

## Como o worker se liga ao back-end

Nada precisa ser configurado: os padrões já apontam para o código do back-end
(`app.models:Alert`, `app.models:User`, `app.models:StockQuote`,
`app.database.session:SessionLocal`).

A cada 5 minutos (`ALERT_CHECK_INTERVAL_MINUTES`) o worker:

1. lê os alertas com `is_active == True` e `is_triggered == False`;
2. consulta cada ticker uma única vez e **grava a cotação em `stock_quotes`**
   (é isso que alimenta `GET /api/stocks/{ticker}` e `/history`);
3. dispara quando `ABOVE` e preço ≥ alvo, ou `BELOW` e preço ≤ alvo;
4. marca `is_triggered = True` e envia o e-mail para `alert.owner.email`.

O alerta é marcado **antes** de enviar o e-mail (UPDATE condicional), então dois
processos nunca mandam o mesmo aviso; se o envio falhar, ele volta a ficar
pendente. A tabela `alerts` não tem `triggered_at`; se alguém adicionar essa
coluna, o worker passa a preenchê-la sozinho.

### Rodar o worker

Em outro terminal, dentro de `backend/`, com a API ligada ou não:

```powershell
python -m app.workers          # roda sempre, a cada 5 minutos
python -m app.workers --once   # um ciclo só
```

O worker é um processo separado que acessa o mesmo `quotly.db`, como previsto
no `GUIA_INTEGRACAO_GRUPO.md`. Não é preciso mexer no `app/main.py`.

## Cotações para a API

O worker grava em `stock_quotes` as cotações dos tickers que têm alerta ativo,
e as rotas existentes `GET /api/stocks/{ticker}` e `/history` passam a devolver
esses dados.

Para consultar **qualquer** ação direto nas APIs de mercado, há um roteador
opcional pronto em `app/routes/quotes.py` (`GET /api/quotes/{ticker}` e
`/api/quotes/{ticker}/history?range=7d|1mo|6mo|1y`, no formato do
`API_CONTRACT.md` do front-end). Ele fica desligado até o responsável pelo
back-end decidir incluí-lo no `app/main.py`; as instruções estão no topo do
arquivo.

## Testes manuais

```powershell
python -m scripts.check_quote PETR4 --history 1mo   # cotação real
python -m scripts.send_test_email voce@email.com     # e-mail de exemplo
python -m scripts.demo_worker voce@email.com         # ciclo completo, banco temporário
```

Para receber o e-mail de verdade: crie uma caixa no [Mailtrap](https://mailtrap.io),
ponha usuário/senha em `.env.worker` e troque `EMAIL_BACKEND=smtp`. Com Gmail:
`SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587` e uma senha de app em `SMTP_PASSWORD`.

## Provedores de cotação

Ordem em `MARKET_PROVIDERS` (padrão `brapi,yfinance`). Sem `BRAPI_TOKEN` a brapi
só responde PETR4, VALE3, MGLU3 e ITUB4 (token gratuito em brapi.dev/dashboard);
o histórico gratuito dela é curto, então períodos longos caem no yfinance.

## Pontos a alinhar com o grupo

- O contrato do front (`API_CONTRACT.md`) e o back-end atual divergem: login
  em JSON × `form-urlencoded`, `status` × `is_triggered/is_active`, `camelCase`
  × `snake_case`, `/api/quotes` × `/api/stocks`. O worker funciona com o
  back-end como está hoje.
- `/api/stocks/{ticker}` devolve o último registro de `stock_quotes`, que só é
  preenchido para tickers com alerta ativo. Para o front consultar qualquer
  ação, o ideal é usar `/api/quotes/{ticker}`.

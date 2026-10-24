# Quotly: contrato da API (front-end ↔ back-end)

> **Proposta do front-end (Integrante 3).** Integrantes 1 e 2: revisem e ajustem o que for preciso.
> Toda mudança aqui precisa ser avisada, porque o front-end depende exatamente destes nomes de campos.

- Base URL (dev): `http://localhost:8000`
- Formato: JSON (`Content-Type: application/json`)
- Autenticação: `Authorization: Bearer <access_token>` em todas as rotas, exceto register/login
- Erros: seguir o padrão do FastAPI → `{ "detail": "mensagem legível em português" }`
- Datas: ISO 8601 (`2026-10-24T18:30:00Z`); datas sem hora como `2026-10-24`
- **CORS:** liberar a origem `http://localhost:5173` (Vite)

---

## Autenticação (Integrante 1)

### `POST /api/auth/register`
```json
// request
{ "name": "Maria", "email": "maria@email.com", "password": "123456" }
// 201
{ "id": 1, "name": "Maria", "email": "maria@email.com" }
// 400 → { "detail": "Este e-mail já está cadastrado." }
```

### `POST /api/auth/login`
Recebe **JSON** (não form-data do OAuth2).
```json
// request
{ "email": "maria@email.com", "password": "123456" }
// 200
{ "access_token": "eyJhbGciOi...", "token_type": "bearer" }
// 401 → { "detail": "E-mail ou senha incorretos." }
```

### `GET /api/auth/me` 🔒
```json
{ "id": 1, "name": "Maria", "email": "maria@email.com" }
```
Token inválido ou expirado → **401** (o front desloga automaticamente).

---

## Cotações (Integrantes 2 e 1)

### `GET /api/quotes/{ticker}` 🔒
```json
{
  "ticker": "PETR4",
  "name": "Petrobras PN",
  "currency": "BRL",
  "price": 38.42,
  "change": 0.57,
  "changePercent": 1.51,
  "previousClose": 37.85,
  "high": 38.90,
  "low": 37.60,
  "volume": 31250000,
  "updatedAt": "2026-10-24T18:30:00Z"
}
```
Ticker inexistente → **404** `{ "detail": "Ativo \"XYZ1\" não encontrado." }`

### `GET /api/quotes/{ticker}/history?range=7d|1mo|6mo|1y` 🔒
Lista em ordem **cronológica crescente**, um ponto por pregão:
```json
[
  { "date": "2026-10-20", "close": 37.10 },
  { "date": "2026-10-21", "close": 37.55 },
  { "date": "2026-10-22", "close": 37.85 }
]
```

---

## Alertas (Integrante 1, verificados pelo worker do Integrante 2)

Objeto `Alert`:
```json
{
  "id": 7,
  "ticker": "PETR4",
  "targetPrice": 40.00,
  "condition": "above",          // "above" (subir acima de) | "below" (cair abaixo de)
  "status": "active",            // "active" | "triggered" | "disabled"
  "createdAt": "2026-10-24T18:30:00Z",
  "triggeredAt": null            // preenchido pelo worker quando dispara o e-mail
}
```

| Método | Rota | Body | Resposta |
|---|---|---|---|
| `GET` | `/api/alerts` 🔒 | — | `Alert[]` do usuário logado |
| `POST` | `/api/alerts` 🔒 | `{ ticker, targetPrice, condition }` | `201` + `Alert` (status `active`) |
| `PATCH` | `/api/alerts/{id}` 🔒 | qualquer subconjunto de `{ ticker, targetPrice, condition, status }` | `Alert` atualizado |
| `DELETE` | `/api/alerts/{id}` 🔒 | — | `204` |

Regras:
- Um usuário só vê, edita e exclui os **próprios** alertas (senão → 404).
- `PATCH` com `status: "active"` reativa um alerta disparado ou desativado (zera `triggeredAt`).
- O worker só verifica alertas com `status = "active"` e, ao disparar, muda para `triggered` e preenche `triggeredAt`.

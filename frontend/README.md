# Quotly: Front-end

SPA em **React + Vite + Tailwind CSS v4**, com React Router, Axios, Recharts e react-hot-toast.

## Como rodar

```bash
cd frontend
npm install
copy .env.example .env      # no Windows (no Linux/Mac: cp .env.example .env)
npm run dev
```

Abra http://localhost:5173.

### Modo mock × API real

No `.env`:

| Variável | Valor | Efeito |
|---|---|---|
| `VITE_USE_MOCK` | `true` | Usa o "back-end falso" em `src/services/mocks/mockServer.js`. Não precisa do back-end. Usuários e alertas ficam no localStorage. |
| `VITE_USE_MOCK` | `false` | Chama a API real em `VITE_API_URL`. |
| `VITE_API_URL` | `http://localhost:8000` | Endereço do back-end. |

Depois de mudar o `.env`, reinicie o `npm run dev`.

No modo mock dá para buscar: PETR4, VALE3, ITUB4, BBDC4, BBAS3, WEGE3, MGLU3, ABEV3, AAPL, MSFT, TSLA, NVDA.
Qualquer outro código retorna "não encontrado", para testar o tratamento de erro.

O formato de cada endpoint está em [`../API_CONTRACT.md`](../API_CONTRACT.md).

## Estrutura

```
src/
├── main.jsx                 # BrowserRouter + AuthProvider + Toaster
├── App.jsx                  # rotas (públicas / privadas)
├── index.css                # Tailwind + cores do tema (up/down/brand)
├── context/
│   └── AuthContext.jsx      # usuário logado, login(), register(), logout()
├── services/
│   ├── api.js               # axios, interceptor JWT, logout no 401, getErrorMessage()
│   ├── auth.js              # register / login / me
│   ├── quotes.js            # cotação + histórico
│   ├── alerts.js            # CRUD de alertas
│   └── mocks/mockServer.js  # back-end falso (mesmo formato da API real)
├── components/
│   ├── Layout.jsx           # navbar + <Outlet/>
│   ├── RouteGuards.jsx      # PrivateRoute / PublicOnlyRoute
│   ├── QuoteCard.jsx        # card de cotação (+ skeleton)
│   ├── PriceChart.jsx       # gráfico de histórico (Recharts) com 7D/1M/6M/1A
│   ├── AlertForm.jsx        # criar/editar alerta, com validação
│   ├── StatusBadge.jsx, Modal.jsx, Button.jsx, FormField.jsx, Spinner.jsx ...
├── pages/
│   ├── Login.jsx, Register.jsx
│   ├── Dashboard.jsx        # busca + card + gráfico + "criar alerta"
│   ├── Alerts.jsx           # lista, filtros, editar, pausar, excluir
│   └── NotFound.jsx
└── utils/format.js          # moeda, %, datas em pt-BR
```

## Checklist (workflow do Integrante 3)

- [x] Setup Vite + Tailwind + rotas `/login`, `/register`, `/dashboard`, `/alerts`
- [x] Login/cadastro com validação e toasts
- [x] Interceptor que anexa o JWT e desloga no 401
- [x] Rotas protegidas
- [x] Busca de ações, card com variação colorida, gráfico interativo com períodos
- [x] Tratamento de ticker não encontrado e de erro de rede
- [x] Formulário de alerta (ticker, preço alvo, condição) com validação
- [x] Lista de alertas com badges de status, filtros, editar, pausar e excluir
- [x] Skeletons e spinners de loading, layout responsivo
- [ ] **Alinhar o `API_CONTRACT.md` com os Integrantes 1 e 2**
- [ ] Testar com `VITE_USE_MOCK=false` e o back-end rodando (fluxo completo)
- [ ] Ajustes finais de visual e apresentação

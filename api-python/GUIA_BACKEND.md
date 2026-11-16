# Guia sobre o backend

Terminei toda a parte central do nosso back-end e banco de dados! Já upei tudo que faltava da API, já testei os endpoints e coloquei a documentação visual automática do FastAPI.

Escrevi esse guia pra explicar como rodar o projeto na máquina de cada um e como cada um vai conectar cada parte.

---

## 🚀 1. Como rodar o servidor no computador

Antes de tudo, puxem as atualizações da branch `feature/backend-core` :

```bash
# Entra na pasta do backend
cd Quotly/backend

# Cria e ativa o ambiente virtual do Python (se ainda não tiverem)
python3 -m venv .venv
source .venv/bin/activate

# Instala as bibliotecas necessárias
pip install -r requirements.txt

# Liga o servidor do backend
uvicorn app.main:app --reload
```

Assim que ligar, abram o navegador em:  
👉 **`http://localhost:8000/docs`**

Vai abrir uma página de testes de endpoints, lá vcs conseguem ver todas as rotas, clicar em **"Try it out"**, testar envios de dados e ver as respostas reais na hora.

---

## 🎨 2. Instruções workflow integrante 3 (Front-end / JavaScript)

Vou explicar como consumir a API no React/Vite:

- **CORS já liberado:** Se o seu front-end rodar em `http://localhost:5173` ou `http://localhost:3000`, o navegador não vai bloquear suas requisições. Já configurei isso no servidor.
- **Como funciona o Login e o Token:**
  1. No cadastro (`POST /api/auth/register`), você manda `{ name, email, password }` (senha no mínimo 8 caracteres).
  2. No login (`POST /api/auth/login`), você manda e-mail e senha. A API te devolve um `access_token` (nosso crachá digital).
  3. Você salva esse token no front (pode ser no `localStorage`).
  4. Nas próximas requisições de rotas fechadas (como criar alerta ou ver perfil), só mandar no cabeçalho da requisição:  
     `Authorization: Bearer <SEU_TOKEN_AQUI>`.
- **Rotas de Ações e Gráficos:**
  - `GET /api/stocks/{ticker}`: Pega o preço mais recente da ação (ex: `/api/stocks/PETR4`).
  - `GET /api/stocks/{ticker}/history`: Te devolve uma lista de preços com datas, prontinha pra você jogar na biblioteca de gráfico e desenhar a linha do tempo!
- **Rotas de Alertas:**
  - `POST /api/alerts/`: Cadastra um alerta novo (`ticker`, `target_price`, `condition: "ABOVE"` ou `"BELOW"`).
  - `GET /api/alerts/`: Lista só os alertas da pessoa que tá logada.
  - `PATCH /api/alerts/{id}`: Liga/desliga o alerta ou muda o preço.
  - `DELETE /api/alerts/{id}`: Apaga o alerta.

---

## ⚙️ 3. Instruções workflow Integrante 2 (Worker de Cotações & E-mails)

A estrutura do banco tá montada pra usar no script de background:

- **Onde buscar o que monitorar:**  
  No banco de dados (`quotly.db`), a tabela `alerts` guarda todos os alertas criados. Você pode fazer um select buscando os alertas ativos que ainda não foram disparados:
  ```python
  # Exemplo usando os modelos criados:
  from app.database.session import SessionLocal
  from app.models.alert import Alert

  db = SessionLocal()
  # Pega os alertas que precisam ser checados
  alertas_ativos = db.query(Alert).filter(Alert.is_active == True, Alert.is_triggered == False).all()
  ```
- **Conexão com a Brapi / API Externa:**  
  Só precisa pegar os tickers únicos dessa lista (ex: `PETR4`, `VALE3`), bater na Brapi pra pegar o preço atual e comparar com o `alerta.target_price`.
- **Como salvar o histórico no banco:**  
  Toda vez que você pegar uma cotação nova na Brapi, salva ela na tabela `stock_quotes` (usando o modelo `StockQuote` ou chamando a rota `POST /api/stocks/`). Isso alimenta o histórico que o front-end vai usar pros gráficos!
- **Disparou o E-mail?:**  
  Assim que o preço atingir a meta e você mandar o e-mail pro dono (`alerta.owner.email`), basta atualizar o alerta no banco:
  ```python
  alerta.is_triggered = True
  db.commit()
  ```
  Isso evita que o mesmo alerta fique mandando 50 e-mails seguidos pro usuário.

---

Qualquer dúvida ou se precisarem de algum campo a mais nas rotas, só me darem um toque que eu mudo. 🚀

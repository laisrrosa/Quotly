# Fala pessoal! 👋 Guia prático do nosso Back-end (Quotly)

Terminei toda a parte central do nosso back-end e banco de dados! A API já tá 100% de pé, testada e com documentação visual automática.

Além disso, para cumprir o requisito do professor de ter **pelo menos um endpoint em Java e endpoints em Python**, adicionei um microsserviço em Java (Spring Boot) focado em **Cálculos e Simulações de Investimento**!

Escrevi este guia rápido e direto ao ponto para explicar como rodar tudo na máquina de vocês e como cada um vai conectar a sua parte sem dor de cabeça.

---

## 🚀 1. Como rodar os servidores no computador de vocês

Puxem as atualizações da branch `feature/backend-core`:

### A) Servidor Core em Python (FastAPI - Porta 8000)
```bash
# Entra na pasta do backend Python
cd Quotly/backend

# Cria e ativa o ambiente virtual do Python (se ainda não tiverem)
python3 -m venv .venv
source .venv/bin/activate

# Instala as bibliotecas necessárias
pip install -r requirements.txt

# Liga o servidor do backend Python
uvicorn app.main:app --reload
```
Acesse a documentação interativa em: 👉 **`http://localhost:8000/docs`**

---

### B) Microsserviço de Analytics em Java (Spring Boot - Porta 8085)
```bash
# Entra na pasta do serviço Java
cd Quotly/analytics-service

# Roda o serviço Java
./gradlew bootRun
```
Ele sobe em menos de 1 segundo na porta `8085`!

---

## 🎨 2. Instruções para o Integrante 3 (Front-end / JavaScript)

Cara, deixei a vida bem fácil pra você consumir as APIs no seu React/Vite:

- **CORS já liberado:** Tanto o Python (porta `8000`) quanto o Java (porta `8085`) já estão com CORS liberado para `http://localhost:5173` e `http://localhost:3000`. O navegador não vai bloquear nada!
- **Como funciona o Login e o Token (Python):**
  1. No cadastro (`POST /api/auth/register`), você manda `{ name, email, password }` (senha no mínimo 8 caracteres).
  2. No login (`POST /api/auth/login`), você manda e-mail e senha. A API te devolve um `access_token` (nosso crachá digital).
  3. Você salva esse token no front (no `localStorage`).
  4. Nas próximas requisições de rotas fechadas (como criar alerta ou ver perfil), basta mandar no cabeçalho da requisição:  
     `Authorization: Bearer <SEU_TOKEN_AQUI>`.
- **Rotas de Ações e Gráficos (Python):**
  - `GET /api/stocks/{ticker}`: Pega o preço mais recente da ação (ex: `/api/stocks/PETR4`).
  - `GET /api/stocks/{ticker}/history`: Te devolve uma lista de preços com datas, prontinha pra você jogar na biblioteca de gráfico e desenhar a linha do tempo!
- **Rotas de Alertas (Python):**
  - `POST /api/alerts/`: Cadastra um alerta novo (`ticker`, `target_price`, `condition: "ABOVE"` ou `"BELOW"`).
  - `GET /api/alerts/`: Lista só os alertas da pessoa que tá logada.
  - `PATCH /api/alerts/{id}`: Liga/desliga o alerta ou muda o preço.
  - `DELETE /api/alerts/{id}`: Apaga o alerta.
- **Rota de Simulação Financeira (JAVA - Porta 8085):**
  - `GET http://localhost:8085/api/analytics/simulate?ticker=PETR4&initialAmount=1000&monthlyContribution=200&months=12&annualRatePercent=12`
  - Você pode criar uma aba ou card simples chamado **"Simulador de Rendimento"** onde o usuário digita esses valores e você exibe o resultado do cálculo de juros compostos que o Java devolve!

---

## ⚙️ 3. Instruções para o Integrante 2 (Worker de Cotações & E-mails)

Irmão, a sua parte continua 100% igual e independente:

- **Onde buscar o que monitorar:**  
  No banco de dados (`quotly.db`), a tabela `alerts` guarda todos os alertas criados. Você pode fazer um select buscando os alertas ativos que ainda não foram disparados:
  ```python
  from app.database.session import SessionLocal
  from app.models.alert import Alert

  db = SessionLocal()
  alertas_ativos = db.query(Alert).filter(Alert.is_active == True, Alert.is_triggered == False).all()
  ```
- **Conexão com a Brapi / API Externa:**  
  Você só precisa pegar os tickers únicos dessa lista (ex: `PETR4`, `VALE3`), bater na Brapi pra pegar o preço atual e comparar com o `alerta.target_price`.
- **Como salvar o histórico no banco:**  
  Toda vez que você pegar uma cotação nova na Brapi, salva ela na tabela `stock_quotes` (usando o modelo `StockQuote` ou chamando a rota `POST /api/stocks/`). Isso alimenta o histórico que o front-end vai usar pros gráficos!
- **Disparou o E-mail?:**  
  Assim que o preço atingir a meta e você mandar o e-mail pro dono (`alerta.owner.email`), basta atualizar o alerta no banco:
  ```python
  alerta.is_triggered = True
  db.commit()
  ```
  Isso evita que o mesmo alerta fique mandando e-mails duplicados pro usuário.

---

Qualquer dúvida ou se precisarem de algum ajuste, só me darem um toque! Tamo junto! 🚀

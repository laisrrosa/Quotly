# SYSTEM SPECIFICATION & IMPLEMENTATION GUIDE: QUOTLY BACKEND & INTEGRATION

**Target Audience:** AI Coding Agents / Autonomous Developers (LLMs)  
**System Architecture:** Polyglot Distributed Microservices (FastAPI Core + Spring Boot Analytics)  
**Status:** Core Backend Completed (100%). Ready for Worker (Member 2) and Frontend (Member 3) consumption.

---

## 1. SYSTEM CONTEXT & TOPOLOGY

```text
[Client / Frontend SPA] (React + Vite, Ports: 5173, 3000)
    │
    ├── HTTP/REST ──> [Core Backend] (Python FastAPI, Port: 8000)
    │                     ├── SQLite Database: quotly.db
    │                     ├── Auth (JWT + Bcrypt)
    │                     ├── Alerts CRUD (Anti-IDOR)
    │                     └── Stocks Cache & History
    │
    └── HTTP/REST ──> [Analytics Microservice] (Java Spring Boot, Port: 8085)
                          └── Financial Simulation Engine (Compound Interest)

[Worker Process] (Python Service - Member 2)
    └── Direct SQLite Access (quotly.db) + External Market API (Brapi) + SMTP
```

---

## 2. ENVIRONMENT INITIALIZATION & EXECUTION PROTOCOL

### Task 2.1: Start Python Core Microservice (FastAPI)
1. Navigate to: `Quotly/backend`
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies from lockfile:
   ```bash
   pip install -r requirements.txt
   ```
4. Verify environment variable presence in `.env`:
   - `SECRET_KEY`: Must be non-empty string.
   - `ALGORITHM`: `"HS256"`
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: `60`
   - `DATABASE_URL`: `"sqlite:///./quotly.db"`
5. Start ASGI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. **Health Check:** `GET http://localhost:8000/` (Expect `status: "online"`, HTTP 200).  
   **API Specification:** `http://localhost:8000/docs` (OpenAPI/Swagger UI).

### Task 2.2: Start Java Analytics Microservice (Spring Boot)
1. Navigate to: `Quotly/analytics-service`
2. Ensure Java 21 runtime is available.
3. Build and run via Gradle Wrapper:
   ```bash
   ./gradlew bootRun
   ```
4. **Health Check:** `GET http://localhost:8085/api/analytics/simulate?ticker=PETR4` (Expect HTTP 200).

---

## 3. MEMBER 3 (FRONT-END DEVELOPER) SPECIFICATION

### Security & Networking Rules
- **CORS Allowed Origins:** `http://localhost:5173`, `http://localhost:3000`, `http://127.0.0.1:5173`, `http://127.0.0.1:3000`.
- **Authentication Scheme:** `Bearer <JWT_TOKEN>` in HTTP Header `Authorization`.

### Endpoint Contract Table

| Action | Method | URL | Headers | Payload (Request) | Expected Response |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Register** | `POST` | `http://localhost:8000/api/auth/register` | `Content-Type: application/json` | `{"name": "str", "email": "str", "password": "str (min 8 chars)"}` | `201 Created`: `{"id": int, "name": str, "email": str, "is_active": bool}` |
| **Login** | `POST` | `http://localhost:8000/api/auth/login` | `Content-Type: application/x-www-form-urlencoded` | `username=<email>&password=<password>` | `200 OK`: `{"access_token": "str", "token_type": "bearer"}` |
| **Get Me** | `GET` | `http://localhost:8000/api/auth/me` | `Authorization: Bearer <TOKEN>` | None | `200 OK`: `{"id": int, "name": str, "email": str}` |
| **Get Quote** | `GET` | `http://localhost:8000/api/stocks/{ticker}` | None | None | `200 OK`: `{"ticker": str, "price": float, "timestamp": str}` |
| **Get History**| `GET` | `http://localhost:8000/api/stocks/{ticker}/history?limit=30` | None | Query param `limit` (1-100) | `200 OK`: `[{"ticker": str, "price": float, "timestamp": str}, ...]` |
| **Create Alert**| `POST`| `http://localhost:8000/api/alerts/` | `Authorization: Bearer <TOKEN>`, `Content-Type: application/json` | `{"ticker": "str", "target_price": float (>0), "condition": "ABOVE"|"BELOW"}` | `201 Created`: Alert object |
| **List Alerts** | `GET` | `http://localhost:8000/api/alerts/` | `Authorization: Bearer <TOKEN>` | None | `200 OK`: Array of Alert objects |
| **Update Alert**| `PATCH`| `http://localhost:8000/api/alerts/{id}` | `Authorization: Bearer <TOKEN>` | `{"target_price": float?, "condition": str?, "is_active": bool?}` | `200 OK`: Updated Alert object |
| **Delete Alert**| `DELETE`| `http://localhost:8000/api/alerts/{id}` | `Authorization: Bearer <TOKEN>` | None | `204 No Content` |
| **Simulation** | `GET` | `http://localhost:8085/api/analytics/simulate` | None | Query params: `ticker`, `initialAmount`, `monthlyContribution`, `months`, `annualRatePercent` | `200 OK`: `{"ticker": str, "totalInvested": float, "totalInterest": float, "finalBalance": float}` |

---

## 4. MEMBER 2 (WORKER & MARKET SERVICE) SPECIFICATION

### Database Schema Interaction Protocol
- **Target File:** `Quotly/backend/quotly.db` (SQLite 3).
- **ORM Models Location:** `Quotly/backend/app/models/`.

### Task Sequence for Background Polling Loop
1. **Instantiate Session:**
   ```python
   import sys
   sys.path.append("/path/to/Quotly/backend")
   from app.database.session import SessionLocal
   from app.models.alert import Alert
   from app.models.stock import StockQuote

   db = SessionLocal()
   ```

2. **Step 1: Extract Active Unnotified Alerts:**
   ```python
   pending_alerts = db.query(Alert).filter(
       Alert.is_active == True,
       Alert.is_triggered == False
   ).all()
   ```

3. **Step 2: Collect Unique Tickers to Minimize External API Calls:**
   ```python
   unique_tickers = list({alert.ticker for alert in pending_alerts})
   ```

4. **Step 3: Fetch Market Data & Persist Snapshot:**
   For each ticker, retrieve current market price from external provider (Brapi / Yahoo Finance) and insert audit row into `stock_quotes`:
   ```python
   snapshot = StockQuote(
       ticker=ticker,
       price=current_price,
       open_price=open_price,
       high_price=high_price,
       low_price=low_price,
       change_percent=change_pct
   )
   db.add(snapshot)
   db.commit()
   ```

5. **Step 4: Evaluate Trigger Conditions & Dispatch Notifications:**
   For each alert in `pending_alerts`:
   ```python
   should_trigger = False
   if alert.condition == "ABOVE" and current_price >= alert.target_price:
       should_trigger = True
   elif alert.condition == "BELOW" and current_price <= alert.target_price:
       should_trigger = True

   if should_trigger:
       # Recipient email is accessible via ORM relationship:
       recipient_email = alert.owner.email
       # Dispatch email via SMTP...
       
       # Mark as triggered to prevent duplicate execution:
       alert.is_triggered = True
       db.commit()
   ```

6. **Step 5: Resource Teardown:**
   Always close DB session in `finally` block:
   ```python
   db.close()
   ```

---

## 5. ERROR HANDLING & STATUS CODES MATRIX

- `400 Bad Request`: Payload validation error, inactive user, duplicate email on register.
- `401 Unauthorized`: Missing, invalid, or expired JWT token; incorrect login credentials.
- `404 Not Found`: Alert or stock record non-existent, or object does not belong to authenticated user (IDOR prevention).
- `422 Unprocessable Entity`: Data type mismatch against Pydantic schema (e.g., negative price, ticker length > 8, history limit > 100).
- `204 No Content`: Successful deletion without response body.

from fastapi import FastAPI

app = FastAPI(title = "Quotly API - Teste", 
              description = "API para teste do Quotly", 
              version = "0.1.0")

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/api/ping")
def ping(nome: str = "Visitante"):
    return {"message": f"Olá {nome}, bem vindo!",
            "resposta": "Pong"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
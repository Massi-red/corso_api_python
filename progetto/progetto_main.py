from .progetto_db import dbInit
from fastapi import FastAPI
from .progetto_prodotti import router as prodotti_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuro il CORS per accettare tutto
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Permette l'accesso da qualsiasi sito (Origin)
    allow_credentials=True,
    allow_methods=["*"],          # Permette tutti i metodi (GET, POST, PUT, DELETE, ecc.)
    allow_headers=["*"],          # Permette tutte le intestazioni (Headers)
)

app.include_router(prodotti_router)

@app.get("/")
def home():
    return {"info":"Server principale attivo"}
            
dbInit()


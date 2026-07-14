from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware

# Importo il resto del progetto
from .progetto_prodotti import router as prodotti_router
from .progetto_utente import router as utente_router
from .progetto_db import dbinit
from .progetto_film import router as film_router
from .progetto_playlist import router as playlist_router

# Inizializzo il DB
dbinit()

# Dichiaro FastAPI
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
app.include_router(utente_router)
app.include_router(film_router)
app.include_router(playlist_router)
# Creo una chiamata base di benvenuto
@app.get("/")
def root():
    return {"messaggio": "Benvenuto!"}

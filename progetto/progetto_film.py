import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3
import json
import urllib.request
import urllib.parse

router = APIRouter()


OMDB_API_KEY = os.environ.get("OMDB_API_KEY")


class FilmIn(BaseModel):
    titolo: str
    trama: Optional[str] = None
    anno: Optional[int] = None
    url_locandina: Optional[str] = None
    tmdb_id: Optional[str] = None


class FilmEsternoImporta(BaseModel):
    imdb_id: str


def _connessione_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def _verifica_chiave_configurata():
    if not OMDB_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Chiave OMDb non configurata. Imposta la variabile d'ambiente OMDB_API_KEY con una chiave gratuita ottenuta su omdbapi.com/apikey.aspx",
        )


def _chiamata_omdb(**parametri):
    parametri["apikey"] = OMDB_API_KEY
    query = urllib.parse.urlencode(parametri)
    url = f"https://www.omdbapi.com/?{query}"

    try:
        with urllib.request.urlopen(url, timeout=10) as risposta:
            return json.load(risposta)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Errore nella chiamata API: {exc}") from exc


@router.get("/film")
def lista_film():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM film")
    risultato = cursor.fetchall()
    conn.close()
    return risultato

@router.get("/film/ricerca")
def cerca_film(keyword: str):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM film WHERE titolo LIKE ?",
        (f"%{keyword}%",)
    )
    risultati = cursor.fetchall()
    conn.close()
    return risultati


@router.get("/film/esterni")
def cerca_film_esterni(keyword: str):
    if not keyword or not keyword.strip():
        raise HTTPException(status_code=400, detail="La keyword è obbligatoria")

    _verifica_chiave_configurata()
    dati = _chiamata_omdb(s=keyword)

    if dati.get("Response") != "True":
        return []

    risultati = []
    for item in dati.get("Search", []):
        risultati.append({
            "titolo": item.get("Title"),
            "anno": item.get("Year"),
            "tipo": item.get("Type"),
            "poster": item.get("Poster"),
            "imdb_id": item.get("imdbID"),
        })

    return risultati


@router.get("/film/{id}")
def get_film(id: int):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM film WHERE id = ?", (id,))
    film = cursor.fetchone()
    conn.close()
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    return film


# Creazione manuale di un film: usata quando l'utente non trova il film cercato
# né nel DB locale né tra i risultati esterni, e vuole aggiungerlo a mano.
@router.post("/film", status_code=201, tags=["film"])
def crea_film(dati: FilmIn):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO film (titolo, trama, anno, url_locandina, tmdb_id) VALUES (?, ?, ?, ?, ?)",
        (dati.titolo, dati.trama, dati.anno, dati.url_locandina, dati.tmdb_id),
    )
    conn.commit()
    nuovo_id = cursor.lastrowid
    conn.close()
    return {"message": "Film aggiunto con successo", "id": nuovo_id, "titolo": dati.titolo}


# Parte OPZIONALE dell'assegnazione: quando l'utente seleziona un film trovato
# tramite l'API esterna, viene automaticamente aggiunto al DB locale prendendo
# le informazioni necessarie dall'API.
@router.post("/film/esterni/importa", status_code=201, tags=["film"])
def importa_film_esterno(dati: FilmEsternoImporta):
    _verifica_chiave_configurata()

    conn = _connessione_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM film WHERE tmdb_id = ?", (dati.imdb_id,))
    esistente = cursor.fetchone()
    if esistente is not None:
        conn.close()
        return {"message": "Il film era già presente nel database locale", "id": esistente["id"], "gia_esistente": True}

    info = _chiamata_omdb(i=dati.imdb_id, plot="full")

    if info.get("Response") != "True":
        conn.close()
        raise HTTPException(status_code=404, detail="Film non trovato su OMDb")

    try:
        anno = int(str(info.get("Year", ""))[:4])
    except (ValueError, TypeError):
        anno = None

    poster = info.get("Poster")
    if poster == "N/A":
        poster = None

    trama = info.get("Plot")
    if trama == "N/A":
        trama = None

    cursor.execute(
        "INSERT INTO film (titolo, trama, anno, url_locandina, tmdb_id) VALUES (?, ?, ?, ?, ?)",
        (info.get("Title"), trama, anno, poster, dati.imdb_id),
    )
    conn.commit()
    nuovo_id = cursor.lastrowid
    conn.close()

    return {"message": "Film importato con successo", "id": nuovo_id, "titolo": info.get("Title"), "gia_esistente": False}
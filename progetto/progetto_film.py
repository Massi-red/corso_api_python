from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3
import json
import urllib.request
import urllib.parse
 
# Creo il mini-gestore delle rotte
router = APIRouter()


class FilmIn(BaseModel):
    titolo: str
    trama: Optional[str] = None
    anno: Optional[int] = None
    url_locandina: Optional[str] = None
    tmdb_id: Optional[str] = None

 
# Espongo la chiamata per listare i prodotti
@router.get("/film")
def lista_film():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM film")
    risultato = cursor.fetchall()
    conn.close()
    return [dict(row) for row in risultato]
 
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
    return [dict(row) for row in risultati]

@router.get("/film/{id}")
def get_film(id: int):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM film WHERE id = ?",
        (id,)
    )
    film = cursor.fetchone()

    conn.close()
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")
    return dict(film)


# Creazione manuale di un film: usata quando l'utente non trova il film cercato
# nel DB locale (né tra i risultati esterni) e vuole aggiungerlo a mano.
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


@router.get("/film/esterni")
def cerca_film_esterni(keyword: str):
    if not keyword or not keyword.strip():
        raise HTTPException(status_code=400, detail="La keyword è obbligatoria")

    query = urllib.parse.quote(keyword)
    url = f"https://www.omdbapi.com/?s={query}&apikey=4f3f3d8b"

    try:
        with urllib.request.urlopen(url, timeout=10) as risposta:
            dati = json.load(risposta)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Errore nella chiamata API: {exc}") from exc

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
    
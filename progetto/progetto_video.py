from typing import Optional

import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class VideoIn(BaseModel):
    url_video_youtube: str
    commento: Optional[str] = None


def _connessione_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def _ottieni_utente_da_token(token: str):
    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM utenti WHERE token = ?", (token,))
    utente = cursor.fetchone()
    conn.close()
    return dict(utente) if utente else None


def _film_esiste(film_id: int) -> bool:
    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM film WHERE id = ?", (film_id,))
    trovato = cursor.fetchone() is not None
    conn.close()
    return trovato


# Lettura pubblica: chiunque può vedere i video/commenti di un film (Lezione 11, Fase 3)
@router.get("/film/{film_id}/video", tags=["video"])
def lista_video_film(film_id: int):
    if not _film_esiste(film_id):
        raise HTTPException(status_code=404, detail="Film non trovato")

    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, film_id, url_video_youtube, commento FROM elementi_video WHERE film_id = ?",
        (film_id,),
    )
    risultati = cursor.fetchall()
    conn.close()
    return [dict(r) for r in risultati]


# Scrittura protetta: solo chi passa un token valido può aggiungere un video/commento
@router.post("/film/{film_id}/video", status_code=201, tags=["video"])
def aggiungi_video_film(film_id: int, token: str, dati: VideoIn):
    utente = _ottieni_utente_da_token(token)
    if utente is None:
        raise HTTPException(status_code=401, detail="Devi effettuare il login per aggiungere un video o un commento.")

    if not _film_esiste(film_id):
        raise HTTPException(status_code=404, detail="Film non trovato")

    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO elementi_video (film_id, url_video_youtube, commento) VALUES (?, ?, ?)",
        (film_id, dati.url_video_youtube, dati.commento),
    )
    conn.commit()
    nuovo_id = cursor.lastrowid
    conn.close()

    return {"message": "Video aggiunto con successo", "id": nuovo_id, "film_id": film_id}


# Rimozione protetta di un video/commento
@router.delete("/film/{film_id}/video/{video_id}", tags=["video"])
def elimina_video(film_id: int, video_id: int, token: str):
    utente = _ottieni_utente_da_token(token)
    if utente is None:
        raise HTTPException(status_code=401, detail="Sessione non valida. Effettua il login.")

    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM elementi_video WHERE id = ? AND film_id = ?", (video_id, film_id))
    conn.commit()
    eliminato = cursor.rowcount > 0
    conn.close()

    if not eliminato:
        raise HTTPException(status_code=404, detail="Video non trovato")

    return {"message": "Video eliminato", "id": video_id}

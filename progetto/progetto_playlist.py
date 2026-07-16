from typing import Optional

import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class PlaylistCrea(BaseModel):
    nome: str
    descrizione: Optional[str] = None
    pubblico: bool = True


class PlaylistAggiorna(BaseModel):
    nome: Optional[str] = None
    descrizione: Optional[str] = None
    pubblico: Optional[bool] = None


class FilmPlaylist(BaseModel):
    film_id: int


def _connessione_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_playlist_db():
    conn = _connessione_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descrizione TEXT,
            proprietario_id INTEGER NOT NULL,
            pubblico INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (proprietario_id) REFERENCES utenti(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlist_film (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            film_id INTEGER NOT NULL,
            FOREIGN KEY (playlist_id) REFERENCES playlist(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


init_playlist_db()


def _ottieni_utente_da_token(token: str):
    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM utenti WHERE token = ?", (token,))
    utente = cursor.fetchone()
    conn.close()
    return dict(utente) if utente else None


def _ottieni_playlist_per_id(playlist_id: int):
    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM playlist WHERE id = ?", (playlist_id,))
    playlist = cursor.fetchone()
    conn.close()
    return dict(playlist) if playlist else None


def _ottieni_film_playlist(playlist_id: int):
    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute("SELECT film_id FROM playlist_film WHERE playlist_id = ?", (playlist_id,))
    film_ids = [row["film_id"] for row in cursor.fetchall()]
    conn.close()
    return film_ids


def _serializza_playlist(playlist):
    return {
        "id": playlist["id"],
        "nome": playlist["nome"],
        "descrizione": playlist["descrizione"],
        "proprietario_id": playlist["proprietario_id"],
        "pubblico": bool(playlist["pubblico"]),
        "film_id": _ottieni_film_playlist(playlist["id"]),
    }


@router.post("/playlist", tags=["playlist"])
def crea_playlist(token: str, dati: PlaylistCrea):
    utente = _ottieni_utente_da_token(token)
    if utente is None:
        raise HTTPException(status_code=401, detail="Sessione non valida. Effettua il login.")

    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO playlist (nome, descrizione, proprietario_id, pubblico) VALUES (?, ?, ?, ?)",
        (dati.nome, dati.descrizione, utente["id"], 1 if dati.pubblico else 0),
    )
    conn.commit()
    playlist_id = cursor.lastrowid
    conn.close()

    return {
        "message": "Playlist creata con successo",
        "playlist_id": playlist_id,
        "nome": dati.nome,
        "pubblico": dati.pubblico,
    }


@router.get("/playlist", tags=["playlist"])
def elenca_playlist():
    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM playlist WHERE pubblico = 1 ORDER BY id DESC")
    playlist = cursor.fetchall()
    conn.close()

    return [_serializza_playlist(row) for row in playlist]


# Mostra solo le playlist create dall'utente loggato (pubbliche + private),
# come richiesto dalla Lezione 11, Fase 3.
@router.get("/playlist/mie", tags=["playlist"])
def elenca_mie_playlist(token: str):
    utente = _ottieni_utente_da_token(token)
    if utente is None:
        raise HTTPException(status_code=401, detail="Sessione non valida. Effettua il login.")

    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM playlist WHERE proprietario_id = ? ORDER BY id DESC", (utente["id"],))
    playlist = cursor.fetchall()
    conn.close()

    return [_serializza_playlist(row) for row in playlist]


@router.get("/playlist/{playlist_id}", tags=["playlist"])
def dettaglio_playlist(playlist_id: int, token: Optional[str] = None):
    playlist = _ottieni_playlist_per_id(playlist_id)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist non trovata")

    utente = _ottieni_utente_da_token(token) if token else None
    is_owner = utente is not None and utente["id"] == playlist["proprietario_id"]

    if not playlist["pubblico"] and not is_owner:
        raise HTTPException(status_code=403, detail="Questa playlist è privata")

    return _serializza_playlist(playlist)


@router.post("/playlist/{playlist_id}/film", tags=["playlist"])
def aggiungi_film_playlist(playlist_id: int, token: str, dati: FilmPlaylist):
    utente = _ottieni_utente_da_token(token)
    if utente is None:
        raise HTTPException(status_code=401, detail="Sessione non valida. Effettua il login.")

    playlist = _ottieni_playlist_per_id(playlist_id)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist non trovata")

    if playlist["proprietario_id"] != utente["id"]:
        raise HTTPException(status_code=403, detail="Solo il proprietario può modificare la playlist")

    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM playlist_film WHERE playlist_id = ? AND film_id = ?",
        (playlist_id, dati.film_id),
    )
    if cursor.fetchone() is not None:
        conn.close()
        raise HTTPException(status_code=400, detail="Il film è già presente nella playlist")

    cursor.execute(
        "INSERT INTO playlist_film (playlist_id, film_id) VALUES (?, ?)",
        (playlist_id, dati.film_id),
    )
    conn.commit()
    conn.close()

    return {"message": "Film aggiunto alla playlist", "playlist_id": playlist_id, "film_id": dati.film_id}


@router.delete("/playlist/{playlist_id}/film/{film_id}", tags=["playlist"])
def rimuovi_film_playlist(playlist_id: int, film_id: int, token: str):
    utente = _ottieni_utente_da_token(token)
    if utente is None:
        raise HTTPException(status_code=401, detail="Sessione non valida. Effettua il login.")

    playlist = _ottieni_playlist_per_id(playlist_id)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist non trovata")

    if playlist["proprietario_id"] != utente["id"]:
        raise HTTPException(status_code=403, detail="Solo il proprietario può modificare la playlist")

    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM playlist_film WHERE playlist_id = ? AND film_id = ?",
        (playlist_id, film_id),
    )
    conn.commit()
    conn.close()

    return {"message": "Film rimosso dalla playlist", "playlist_id": playlist_id, "film_id": film_id}


@router.put("/playlist/{playlist_id}", tags=["playlist"])
def aggiorna_playlist(playlist_id: int, token: str, dati: PlaylistAggiorna):
    utente = _ottieni_utente_da_token(token)
    if utente is None:
        raise HTTPException(status_code=401, detail="Sessione non valida. Effettua il login.")

    playlist = _ottieni_playlist_per_id(playlist_id)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist non trovata")

    if playlist["proprietario_id"] != utente["id"]:
        raise HTTPException(status_code=403, detail="Solo il proprietario può modificare la playlist")

    conn = _connessione_db()
    cursor = conn.cursor()

    if dati.nome is not None:
        cursor.execute("UPDATE playlist SET nome = ? WHERE id = ?", (dati.nome, playlist_id))
    if dati.descrizione is not None:
        cursor.execute("UPDATE playlist SET descrizione = ? WHERE id = ?", (dati.descrizione, playlist_id))
    if dati.pubblico is not None:
        cursor.execute("UPDATE playlist SET pubblico = ? WHERE id = ?", (1 if dati.pubblico else 0, playlist_id))

    conn.commit()
    conn.close()

    return {"message": "Playlist aggiornata", "playlist_id": playlist_id}


@router.delete("/playlist/{playlist_id}", tags=["playlist"])
def elimina_playlist(playlist_id: int, token: str):
    utente = _ottieni_utente_da_token(token)
    if utente is None:
        raise HTTPException(status_code=401, detail="Sessione non valida. Effettua il login.")

    playlist = _ottieni_playlist_per_id(playlist_id)
    if playlist is None:
        raise HTTPException(status_code=404, detail="Playlist non trovata")

    if playlist["proprietario_id"] != utente["id"]:
        raise HTTPException(status_code=403, detail="Solo il proprietario può modificare la playlist")

    conn = _connessione_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM playlist WHERE id = ?", (playlist_id,))
    conn.commit()
    conn.close()

    return {"message": "Playlist eliminata", "playlist_id": playlist_id}

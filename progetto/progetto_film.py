from fastapi import APIRouter, HTTPException
import sqlite3
 
# Creo il mini-gestore delle rotte
router = APIRouter()
 
# Espongo la chiamata per listare i prodotti
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
    return film
    
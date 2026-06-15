from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

# Genero il database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS prodotti (
id INTEGER PRIMARY KEY AUTOINCREMENT,
nome TEXT NOT NULL,
prezzo REAL
)
""")
conn.commit()

# Controllo se è vuoto
cursor.execute("SELECT * FROM prodotti")
risultato = cursor.fetchall()

# Se vuoto lo popolo con dei dati di esempio
if not risultato:
    lista_prodotti = [
        ("Mouse Wireless", 25.50),
        ("Tastiera Meccanica", 89.90),
        ("Monitor 24 Pollici", 149.00),
        ("Cuffie Gaming", 45.00),
        ("Tappetino XL", 15.00)
    ]
    cursor.executemany("INSERT INTO prodotti (nome, prezzo) VALUES (?, ?)", lista_prodotti)
    conn.commit()

# Chiudiamo la connessione iniziale globale
conn.close()

# Dichiaro l'oggetto per validare le richieste
class ProdottoIn(BaseModel):
    nome: str
    prezzo: float

# Dichiaro FastAPI
app = FastAPI()

# Creo una chiamata base di benvenuto
@app.get("/")
def root():
    return {"messaggio": "Benvenuto!"}

# Espongo la chiamata per listare i prodotti
@app.get("/prodotti")
def lista_prodotti():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prodotti")
    risultato = cursor.fetchall()
    conn.close()
    return risultato

# Espongo la chiamata per listare uno specifico prodotto
@app.get("/prodotti/{id_prodotto}")
def lista_prodotto_singolo(id_prodotto: int):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prodotti WHERE id = ?", (id_prodotto,))
    risultato = cursor.fetchone() # fetchone() restituisce None se vuoto
    conn.close()
    
    if risultato is None:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
    return risultato

# Espongo la chiamata per inserire un nuovo prodotto
@app.post("/prodotti", status_code=201)
def crea_prodotto(dati: ProdottoIn):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO prodotti (nome, prezzo) VALUES (?, ?)", (dati.nome, dati.prezzo))
    conn.commit()
    conn.close()
    return {"status": "Prodotto registrato con successo"}

# Espongo la chiamata per modificare un prodotto
@app.put("/prodotti/{id_prodotto}") 
def aggiorna_prodotto(id_prodotto: int, dati: ProdottoIn):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Verifico se il prodotto richiesto esiste
    cursor.execute("SELECT * FROM prodotti WHERE id = ?", (id_prodotto,))
    risultato = cursor.fetchone()
    if risultato is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
    
    cursor.execute("UPDATE prodotti SET nome = ?, prezzo = ? WHERE id = ?", (dati.nome, dati.prezzo, id_prodotto))
    conn.commit()
    conn.close()
    return {"status": "Modifica salvata"}

# Espongo la chiamata per cancellare un prodotto
@app.delete("/prodotti/{id_prodotto}")
def elimina(id_prodotto: int):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Verifico se il prodotto richiesto esiste
    cursor.execute("SELECT * FROM prodotti WHERE id = ?", (id_prodotto,))
    risultato = cursor.fetchone()
    if risultato is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
    
    cursor.execute("DELETE FROM prodotti WHERE id=?", (id_prodotto,))
    conn.commit()
    conn.close()
    return {"status": "Cancellato"}
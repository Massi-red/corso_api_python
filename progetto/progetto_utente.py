from .progetto_classi_validazione import UtenteAuth
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import hashlib
import secrets

# Creo il mini-gestore delle rotte
router = APIRouter()

def calcola_hash(password_chiaro: str) -> str:
    # Trasformiamo la stringa di testo in byte (formato UTF-8)
    password_bytes = password_chiaro.encode('utf-8')
    # Calcoliamo lo SHA-256 e restituiamo il codice esadecimale finale
    return hashlib.sha256(password_bytes).hexdigest()

@router.post("/register")
def registra_utente(dati: UtenteAuth):
    # Cifriamo la password prima di mandarla al database
    password_sicura = calcola_hash(dati.password)
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    try:
        # Inseriamo i dati usando i segnaposto sicuri ? contro le SQL Injection
        cursor.execute(
            "INSERT INTO utenti (username, password_hash) VALUES (?, ?)", 
            (dati.username, password_sicura)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Se lo username esiste già nel database (vincolo UNIQUE violato)
        conn.close()
        raise HTTPException(status_code=400, detail="Questo username è già occupato. Scegline un altro.")
    
    conn.close()
    return {"status": "Utente registrato con successo!"}

@router.post("/login")
def login_utente(dati: UtenteAuth):
    # Calcoliamo l'hash della password scritta nel form sul momento
    hash_da_verificare = calcola_hash(dati.password)
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Cerchiamo se esiste lo username sul database
    cursor.execute("SELECT id, password_hash FROM utenti WHERE username = ?", (dati.username,))
    utente = cursor.fetchone()
    
    # Controllo di sicurezza: se l'utente non c'è o l'hash nel DB è diverso da quello inserito
    if utente is None or utente[1] != hash_da_verificare:
        conn.close()
        raise HTTPException(status_code=401, detail="Credenziali non valide. Controlla username e password.")
    
    # --- LOGICA DI SESSIONE SICURA CON TOKEN ---
    # Generiamo un pass casuale esadecimale imbrogliabile di 32 caratteri (secrets.token_hex)
    token_sessione = secrets.token_hex(16)
    
    # Salviamo il token generato associandolo alla riga di questo utente sul database
    cursor.execute("UPDATE utenti SET token = ? WHERE id = ?", (token_sessione, utente[0]))
    conn.commit()
    conn.close()
    
    # Restituiamo al browser solo il token di accesso (l'ID resta segreto)
    return {"status": "Login effettuato con successo", "token": token_sessione}


# FASE 5 / ESERCITAZIONE 5: Esempio di rotta protetta dal Token
@router.get("/profilo")
def mostra_profilo_utente(token: str): # FastAPI cattura il token dall'URL (?token=...)
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row # RowFactory per mappare i risultati come dizionari
    cursor = conn.cursor()
    
    # Chiediamo al server SQLite a chi appartiene questo pass anonimo
    cursor.execute("SELECT id, username FROM utenti WHERE token = ?", (token,))
    utente_trovato = cursor.fetchone()
    conn.close()
    
    # Se il token non corrisponde a nessuna sessione attiva
    if utente_trovato is None:
        raise HTTPException(status_code=401, detail="Sessione non valida o scaduta. Effettua nuovamente il login.")
    
    # Se è valido, restituiamo i dati personali protetti associati all'utente
    return {
        "messaggio": "Accesso consentito all'area riservata",
        "utente_id": utente_trovato["id"],
        "username": utente_trovato["username"]
    }
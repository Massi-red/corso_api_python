from pydantic import BaseModel

# Dichiaro l'oggetto per validare le richieste
class ProdottoIn(BaseModel):
    nome: str
    prezzo: float

class UtenteAuth(BaseModel):
    username: str
    password: str
import sqlite3
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

lista_prodotti = [
("Mouse Wireless", 25.50),
("Tastiera Meccanica", 89.90),
("Monitor 24 Pollici", 149.00),
("Cuffie Gaming", 45.00),
("Tappetino XL", 15.00)
]
cursor.executemany("INSERT INTO prodotti (nome, prezzo) VALUES (?, ?)", lista_prodotti)
conn.commit()
conn.close()
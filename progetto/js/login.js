const API_URL = "https://effective-space-barnacle-qv775v5wqgpgfpr6-8000.app.github.dev";

async function eseguiRegistrazione() {
    let user = document.getElementById("regUser").value;
    let pass = document.getElementById("regPass").value;

    if (!user || !pass) { alert("Compila entrambi i campi!"); return; }

    let risposta = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: user, password: pass })
    });

    let dati = await risposta.json();

    if (risposta.ok) {
        alert("Ottimo! " + dati.status);
        document.getElementById("regUser").value = "";
        document.getElementById("regPass").value = "";
    } else {
        alert("Errore: " + dati.detail);
    }
}

async function eseguiLogin() {
    let user = document.getElementById("logUser").value;
    let pass = document.getElementById("logPass").value;

    if (!user || !pass) { alert("Inserisci le tue credenziali!"); return; }

    let risposta = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: user, password: pass })
    });

    let dati = await risposta.json();

    if (risposta.ok) {
        localStorage.setItem("session_token", dati.token);
        alert("Accesso autorizzato! Il token è stato memorizzato nel browser.");
        document.getElementById("logUser").value = "";
        document.getElementById("logPass").value = "";
    } else {
        alert("Accesso negato: " + dati.detail);
    }
}

async function controllaMioProfilo() {
    let tokenSalvato = localStorage.getItem("session_token");
    let outputBox = document.getElementById("boxRisultato");

    if (!tokenSalvato) {
        outputBox.className = "result-box result-err";
        outputBox.textContent = "Bloccato! Non hai nessun token nel browser. Effettua prima il login.";
        return;
    }

    let risposta = await fetch(`${API_URL}/profilo?token=${tokenSalvato}`);
    let dati = await risposta.json();

    if (risposta.ok) {
        outputBox.className = "result-box result-ok";
        outputBox.textContent = `Successo! Server dice: Benvenuto Utente #${dati.utente_id} (${dati.username})`;
    } else {
        outputBox.className = "result-box result-err";
        outputBox.textContent = "Errore Server 401: " + dati.detail;
    }
}

function eseguiLogout() {
    localStorage.removeItem("session_token");
    document.getElementById("boxRisultato").textContent = "";
    alert("Sessione chiusa. Il token è stato rimosso dal localStorage.");
}

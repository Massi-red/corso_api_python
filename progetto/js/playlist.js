const API_URL = "https://effective-space-barnacle-qv775v5wqgpgfpr6-8000.app.github.dev";
let playlistApertaId = null;

window.onload = () => {
    const token = localStorage.getItem("session_token");
    if (!token) {
        document.getElementById("messaggioLogin").style.display = "block";
        return;
    }
    document.getElementById("areaPlaylist").style.display = "block";
    caricaMiePlaylist();
};

async function creaPlaylist() {
    const token = localStorage.getItem("session_token");
    const nome = document.getElementById("nuovoNome").value;
    const descrizione = document.getElementById("nuovaDescrizione").value;
    const pubblico = document.getElementById("nuovoPubblico").checked;

    if (!nome.trim()) {
        alert("Inserisci un nome per la playlist!");
        return;
    }

    const risposta = await fetch(`${API_URL}/playlist?token=${token}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome, descrizione: descrizione || null, pubblico })
    });

    const dati = await risposta.json();
    if (risposta.ok) {
        document.getElementById("nuovoNome").value = "";
        document.getElementById("nuovaDescrizione").value = "";
        await caricaMiePlaylist();
    } else {
        alert("Errore: " + dati.detail);
    }
}

async function caricaMiePlaylist() {
    const token = localStorage.getItem("session_token");
    const contenitore = document.getElementById("listaPlaylist");
    contenitore.innerHTML = "Caricamento...";

    try {
        const risposta = await fetch(`${API_URL}/playlist/mie?token=${token}`);
        const playlist = await risposta.json();

        if (!risposta.ok) {
            contenitore.innerHTML = `<p class="empty-note">Errore: ${playlist.detail}</p>`;
            return;
        }

        if (playlist.length === 0) {
            contenitore.innerHTML = "<p class='empty-note'>Non hai ancora creato nessuna playlist.</p>";
            return;
        }

        contenitore.innerHTML = "";
        playlist.forEach(p => {
            const divP = document.createElement("div");
            divP.className = "playlist-card";
            divP.innerHTML = `
                <h4>${p.nome} ${p.pubblico ? "" : "🔒"}</h4>
                <p>${p.descrizione || ""}</p>
                <div class="count">${p.film_id.length} film</div>
            `;
            divP.onclick = () => apriDettaglioPlaylist(p.id);
            contenitore.appendChild(divP);
        });
    } catch (errore) {
        console.error("Errore:", errore);
        contenitore.innerHTML = "<p class='empty-note'>Errore nel caricamento delle playlist.</p>";
    }
}

async function apriDettaglioPlaylist(idPlaylist) {
    const token = localStorage.getItem("session_token");
    playlistApertaId = idPlaylist;

    const risposta = await fetch(`${API_URL}/playlist/${idPlaylist}?token=${token}`);
    const playlist = await risposta.json();

    if (!risposta.ok) {
        alert("Errore: " + playlist.detail);
        return;
    }

    document.getElementById("dettaglioNome").textContent = playlist.nome;
    document.getElementById("dettaglioDescrizione").textContent = playlist.descrizione || "";
    document.getElementById("dettaglioPlaylist").style.display = "block";
    document.getElementById("dettaglioPlaylist").scrollIntoView({ behavior: "smooth", block: "start" });
    document.getElementById("risultatiRicercaFilm").innerHTML = "";
    document.getElementById("campoCercaFilm").value = "";

    await mostraFilmPlaylist(playlist.film_id);
}

async function mostraFilmPlaylist(filmIds) {
    const lista = document.getElementById("dettaglioFilmLista");
    lista.innerHTML = "";

    if (filmIds.length === 0) {
        lista.innerHTML = "<li class='empty-note' style='background:none; border:none;'>Nessun film ancora inserito.</li>";
        return;
    }

    for (const idFilm of filmIds) {
        try {
            const risposta = await fetch(`${API_URL}/film/${idFilm}`);
            const film = await risposta.json();
            const li = document.createElement("li");
            li.innerHTML = `<span>${film.titolo} (${film.anno})</span>
                <button class="btn btn-danger btn-sm" onclick="rimuoviFilmDaPlaylist(${idFilm})">Rimuovi</button>`;
            lista.appendChild(li);
        } catch (errore) {
            console.error("Errore nel recupero del film:", errore);
        }
    }
}

async function cercaFilmPerPlaylist() {
    const keyword = document.getElementById("campoCercaFilm").value;
    const contenitore = document.getElementById("risultatiRicercaFilm");

    if (!keyword.trim()) {
        alert("Inserisci un testo per la ricerca!");
        return;
    }

    const risposta = await fetch(`${API_URL}/film/ricerca?keyword=${encodeURIComponent(keyword)}`);
    const risultati = await risposta.json();

    contenitore.innerHTML = "";

    if (risultati.length === 0) {
        contenitore.innerHTML = "<p class='empty-note'>Nessun film trovato nel database locale. Puoi aggiungerlo manualmente qui sotto.</p>";
        return;
    }

    risultati.forEach(film => {
        const divFilm = document.createElement("div");
        divFilm.innerHTML = `<span>${film.titolo} (${film.anno})</span>
            <button class="btn btn-outline btn-sm" onclick="aggiungiFilmAllaPlaylist(${film.id})">Aggiungi</button>`;
        contenitore.appendChild(divFilm);
    });
}

async function aggiungiFilmAllaPlaylist(idFilm) {
    const token = localStorage.getItem("session_token");

    const risposta = await fetch(`${API_URL}/playlist/${playlistApertaId}/film?token=${token}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ film_id: idFilm })
    });

    const dati = await risposta.json();
    if (risposta.ok) {
        await apriDettaglioPlaylist(playlistApertaId);
    } else {
        alert("Errore: " + dati.detail);
    }
}

async function rimuoviFilmDaPlaylist(idFilm) {
    const token = localStorage.getItem("session_token");

    const risposta = await fetch(`${API_URL}/playlist/${playlistApertaId}/film/${idFilm}?token=${token}`, {
        method: "DELETE"
    });

    const dati = await risposta.json();
    if (risposta.ok) {
        await apriDettaglioPlaylist(playlistApertaId);
    } else {
        alert("Errore: " + dati.detail);
    }
}

async function aggiungiFilmManuale() {
    const token = localStorage.getItem("session_token");
    const titolo = document.getElementById("manualeTitolo").value;
    const anno = document.getElementById("manualeAnno").value;
    const urlLocandina = document.getElementById("manualeLocandina").value;
    const trama = document.getElementById("manualeTrama").value;

    if (!titolo.trim()) {
        alert("Inserisci almeno il titolo del film!");
        return;
    }

    const rispostaCrea = await fetch(`${API_URL}/film`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            titolo,
            trama: trama || null,
            anno: anno ? parseInt(anno) : null,
            url_locandina: urlLocandina || null
        })
    });

    const filmCreato = await rispostaCrea.json();
    if (!rispostaCrea.ok) {
        alert("Errore nella creazione del film: " + filmCreato.detail);
        return;
    }

    await aggiungiFilmAllaPlaylist(filmCreato.id);

    document.getElementById("manualeTitolo").value = "";
    document.getElementById("manualeAnno").value = "";
    document.getElementById("manualeLocandina").value = "";
    document.getElementById("manualeTrama").value = "";
}

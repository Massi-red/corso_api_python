const API_URL = "https://effective-space-barnacle-qv775v5wqgpgfpr6-8000.app.github.dev";
let filmSelezionatoId = null;

async function avviaRicerca() {
    const keyword = document.getElementById("campoCerca").value;

    if (!keyword.trim()) {
        alert("Inserisci un testo per la ricerca!");
        return;
    }

    try {
        document.getElementById("schedaFilm").style.display = "none";

        const response = await fetch(`${API_URL}/film/ricerca?keyword=${encodeURIComponent(keyword)}`);
        const risultati = await response.json();

        const contenitore = document.getElementById("risultati");
        contenitore.innerHTML = "";

        if (risultati.length === 0) {
            contenitore.innerHTML = "<p class='empty-note'>Nessun film trovato nel database locale.</p>";
            return;
        }

        risultati.forEach((film, indice) => {
            const divFilm = document.createElement("div");
            divFilm.className = "film-card";
            const numero = String(indice + 1).padStart(2, "0");
            divFilm.innerHTML = `
                <span class="frame-tag">No. ${numero}</span>
                ${film.url_locandina ? `<img src="${film.url_locandina}" alt="${film.titolo}">` : `<div style="aspect-ratio:2/3; background:#E4E4DC; margin-bottom:10px;"></div>`}
                <h3>${film.titolo}</h3>
                <div class="year">${film.anno || ""}</div>
            `;
            divFilm.onclick = () => apriScheda(film.id);
            contenitore.appendChild(divFilm);
        });

    } catch (errore) {
        console.error("Errore:", errore);
        document.getElementById("risultati").innerHTML = "<p class='empty-note'>Errore durante la ricerca.</p>";
    }
}

async function apriScheda(idFilm) {
    try {
        const response = await fetch(`${API_URL}/film/${idFilm}`);
        const film = await response.json();

        filmSelezionatoId = film.id;

        document.getElementById("schedaTitolo").textContent = film.titolo;
        document.getElementById("schedaAnno").textContent = film.anno;
        document.getElementById("schedaTrama").textContent = film.trama;

        const immagine = document.getElementById("schedaImmagine");
        if (film.url_locandina) {
            immagine.src = film.url_locandina;
            immagine.style.display = "block";
        } else {
            immagine.src = "";
            immagine.style.display = "none";
        }

        document.getElementById("schedaFilm").style.display = "block";
        document.getElementById("schedaFilm").scrollIntoView({ behavior: "smooth", block: "start" });

        await caricaVideo(idFilm);
    } catch (errore) {
        console.error("Errore:", errore);
        alert("Errore nel recupero dei dettagli del film.");
    }
}

async function caricaVideo(idFilm) {
    const contenitore = document.getElementById("listaVideo");
    contenitore.innerHTML = "Caricamento...";

    try {
        const risposta = await fetch(`${API_URL}/film/${idFilm}/video`);
        const video = await risposta.json();

        if (video.length === 0) {
            contenitore.innerHTML = "<p class='empty-note'>Nessun video o commento ancora presente. Sii il primo!</p>";
            return;
        }

        contenitore.innerHTML = "";
        video.forEach(v => {
            const divVideo = document.createElement("div");
            divVideo.className = "video-item";
            divVideo.innerHTML = `
                <a href="${v.url_video_youtube}" target="_blank">${v.url_video_youtube}</a>
                ${v.commento ? `<p>${v.commento}</p>` : ""}
            `;
            contenitore.appendChild(divVideo);
        });
    } catch (errore) {
        console.error("Errore:", errore);
        contenitore.innerHTML = "<p class='empty-note'>Errore nel caricamento dei video.</p>";
    }
}

async function aggiungiVideo() {
    const tokenSalvato = localStorage.getItem("session_token");

    if (!tokenSalvato) {
        alert("Devi prima effettuare il login per aggiungere un video o un commento!");
        return;
    }

    const url = document.getElementById("nuovoVideoUrl").value;
    const commento = document.getElementById("nuovoVideoCommento").value;

    if (!url.trim()) {
        alert("Inserisci un link YouTube valido!");
        return;
    }

    try {
        const risposta = await fetch(`${API_URL}/film/${filmSelezionatoId}/video?token=${tokenSalvato}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url_video_youtube: url, commento: commento || null })
        });

        const dati = await risposta.json();

        if (risposta.ok) {
            document.getElementById("nuovoVideoUrl").value = "";
            document.getElementById("nuovoVideoCommento").value = "";
            await caricaVideo(filmSelezionatoId);
        } else {
            alert("Errore: " + dati.detail);
        }
    } catch (errore) {
        console.error("Errore:", errore);
        alert("Errore durante l'invio del video.");
    }
}

async function avviaRicercaEsterna() {
    const keyword = document.getElementById("campoCercaEsterno").value;
    const contenitore = document.getElementById("risultatiEsterni");

    if (!keyword.trim()) {
        alert("Inserisci un testo per la ricerca online!");
        return;
    }

    contenitore.innerHTML = "Ricerca in corso...";

    try {
        const risposta = await fetch(`${API_URL}/film/esterni?keyword=${encodeURIComponent(keyword)}`);
        const risultati = await risposta.json();

        if (!risposta.ok) {
            contenitore.innerHTML = `<p class="empty-note">Errore: ${risultati.detail}</p>`;
            return;
        }

        if (risultati.length === 0) {
            contenitore.innerHTML = "<p class='empty-note'>Nessun risultato trovato online.</p>";
            return;
        }

        contenitore.innerHTML = "";
        risultati.forEach(film => {
            const div = document.createElement("div");
            div.className = "external-card";
            const poster = (film.poster && film.poster !== "N/A") ? film.poster : "";
            div.innerHTML = `
                ${poster ? `<img src="${poster}" alt="${film.titolo}">` : `<div style="width:44px;height:64px;background:#E4E4DC;"></div>`}
                <div class="info">
                    <strong>${film.titolo}</strong>
                    <span>${film.anno} — ${film.tipo}</span>
                </div>
                <button class="btn btn-outline btn-sm" onclick="importaFilmEsterno('${film.imdb_id}')">Importa</button>
            `;
            contenitore.appendChild(div);
        });
    } catch (errore) {
        console.error("Errore:", errore);
        contenitore.innerHTML = "<p class='empty-note'>Errore durante la ricerca online.</p>";
    }
}

async function importaFilmEsterno(imdbId) {
    try {
        const risposta = await fetch(`${API_URL}/film/esterni/importa`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ imdb_id: imdbId })
        });

        const dati = await risposta.json();

        if (risposta.ok) {
            alert(dati.gia_esistente ? "Il film era già presente nel database locale." : `"${dati.titolo}" importato con successo nel database locale!`);
            document.getElementById("campoCerca").value = dati.titolo;
            await avviaRicerca();
        } else {
            alert("Errore: " + dati.detail);
        }
    } catch (errore) {
        console.error("Errore:", errore);
        alert("Errore durante l'importazione del film.");
    }
}

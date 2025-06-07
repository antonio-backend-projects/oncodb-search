Perfetto! Ecco una guida completa per configurare Qdrant in locale usando Docker, con persistenza dei dati e due modalità di avvio: **demone (detached)** e **con shell interattiva**.

---

# Guida Configurazione Qdrant con Docker in Locale (Persistente)

---

## 1. Prerequisiti

* Docker installato e funzionante
  [Install Docker](https://docs.docker.com/get-docker/)
* (Opzionale) Docker Compose se vuoi usarlo per gestione servizi multipli

---

## 2. Preparare la directory per la persistenza dati

Per mantenere i dati anche dopo lo spegnimento del container, serve montare un volume o una cartella locale:

```bash
mkdir -p ~/qdrant_data/storage
```

* `~/qdrant_data/storage` è la cartella dove Qdrant salverà i dati su disco fisico

---

## 3. Avvio Qdrant in modalità demone (detached)

Questo comando avvia Qdrant come container in background:

```bash
docker run -d --name qdrant_local \
  -p 6333:6333 \
  -v ~/qdrant_data/storage:/qdrant/storage \
  qdrant/qdrant
```

**Spiegazione:**

* `-d`: avvio in modalità detached (demone)
* `--name qdrant_local`: nome del container
* `-p 6333:6333`: mappa la porta 6333 del container sulla porta 6333 locale
* `-v ~/qdrant_data/storage:/qdrant/storage`: monta la cartella locale per persistenza dati
* `qdrant/qdrant`: immagine ufficiale Qdrant dal Docker Hub

---

## 4. Avvio Qdrant con shell interattiva (per debug, testing)

Se vuoi aprire la shell del container per vedere i log e interagire:

```bash
docker run --rm -it --name qdrant_shell \
  -p 6333:6333 \
  -v ~/qdrant_data/storage:/qdrant/storage \
  qdrant/qdrant
```

* `--rm`: elimina il container quando esci
* `-it`: interattivo con terminale
* Resta in primo piano fino a quando non chiudi (CTRL+C)

---

## 5. Controllare lo stato del container

Per vedere i container attivi:

```bash
docker ps
```

Per vedere tutti i container (anche quelli fermi):

```bash
docker ps -a
```

Per fermare il container in background:

```bash
docker stop qdrant_local
```

Per avviare un container fermato:

```bash
docker start qdrant_local
```

---

## 6. Verifica che Qdrant sia attivo

Apri il browser o usa curl per verificare la connessione:

```bash
curl http://localhost:6333/collections
```

Se non ci sono ancora collezioni, risponderà con `{ "collections": [] }` o simile.

---

## 7. (Opzionale) Comandi utili

* Vedere i log del container in background:

```bash
docker logs -f qdrant_local
```

* Accedere alla shell del container in esecuzione:

```bash
docker exec -it qdrant_local /bin/sh
```

Ecco un file `docker-compose.yml` pronto per avviare Qdrant in locale con persistenza dati, esposto sulla porta 6333:

```yaml
version: "3.8"

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant_local
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_data/storage:/qdrant/storage
    restart: unless-stopped
```

---

### Come usarlo

1. Crea una cartella di lavoro, per esempio `qdrant_project`:

```bash
mkdir -p qdrant_project/qdrant_data/storage
cd qdrant_project
```

2. Salva il file `docker-compose.yml` dentro `qdrant_project`.

3. Avvia Qdrant con:

```bash
docker-compose up -d
```

4. Controlla i log:

```bash
docker-compose logs -f
```

5. Per fermare e rimuovere i container (senza cancellare i dati):

```bash
docker-compose down
```

---

### Note

* La persistenza è garantita montando `./qdrant_data/storage` sulla cartella `/qdrant/storage` nel container.
* La porta 6333 è esposta per permettere alle tue app di connettersi tramite `http://localhost:6333`.
* `restart: unless-stopped` fa sì che il container si riavvii automaticamente in caso di crash o al riavvio del sistema, fino a quando non lo fermi manualmente.

---

Se vuoi, ti posso aiutare a estendere il `docker-compose.yml` per includere anche altri servizi in futuro. Vuoi?



---

## Riepilogo

| Modalità          | Comando docker run                                                                                      | Persistenza dati      | Uso tipico             |
| ----------------- | ------------------------------------------------------------------------------------------------------- | --------------------- | ---------------------- |
| Demone            | `docker run -d --name qdrant_local -p 6333:6333 -v ~/qdrant_data/storage:/qdrant/storage qdrant/qdrant` | Sì (cartella montata) | Servizio sempre attivo |
| Shell interattiva | `docker run --rm -it -p 6333:6333 -v ~/qdrant_data/storage:/qdrant/storage qdrant/qdrant`               | Sì (cartella montata) | Debug / test manuale   |

---

Se vuoi posso prepararti anche un `docker-compose.yml` per gestire Qdrant in modo più semplice con un comando solo. Vuoi?

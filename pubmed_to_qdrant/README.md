Eccoti un README dettagliato per il tuo script di caricamento articoli PubMed su Qdrant con embedding semantico:

---

# PubMed Articles to Qdrant Vector Search

Script Python per generare embedding semantici da articoli PubMed (titolo + abstract) usando `sentence-transformers/all-MiniLM-L6-v2` e caricarli in una collezione Qdrant per ricerche intelligenti.

---

## Funzionalità

* Carica articoli da file JSON (esportati da scraping PubMed)
* Genera embedding vettoriali concatenando titolo e abstract
* Crea automaticamente la collezione Qdrant se non esiste
* Inserisce i dati in Qdrant con payload completo (titolo, abstract, autori, pub\_date, pmid)
* Supporta URL Qdrant e autenticazione tramite API key da variabili `.env`

---

## Requisiti

* Python 3.8+
* Librerie Python:

  * `sentence-transformers`
  * `qdrant-client`
  * `python-dotenv`
* Qdrant server attivo e raggiungibile (default `http://localhost:6333`)

---

## Installazione

1. Clona il repository o copia lo script nel tuo progetto
2. Crea un ambiente virtuale e installa dipendenze:

```bash
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows

pip install sentence-transformers qdrant-client python-dotenv
```

3. Crea un file `.env` nella stessa cartella dello script con:

```env
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=     # Se non usi autenticazione, lascia vuoto
```

---

## Uso

* Prepara un file JSON con gli articoli PubMed, formato esempio:

```json
[
  {
    "title": "The current landscape of neoadjuvant therapy for resectable colon cancer.",
    "abstract": "Neoadjuvant therapy has been proposed...",
    "authors": ["Mei Chan", "Tharani Krishnan", "..."],
    "pub_date": "2025-Jun-06",
    "pmid": "40478728"
  },
  ...
]
```

* Esegui lo script:

```bash
python pubmed_to_qdrant.py
```

Lo script:

* verifica se la collezione `pubmed_articles` esiste su Qdrant e la crea se necessario
* genera embedding per titolo + abstract
* carica batch di articoli in Qdrant con payload

---

## Come funziona internamente

1. **Embedding**: usa `sentence-transformers/all-MiniLM-L6-v2`, modello leggero ed efficace, per trasformare testo in vettori numerici 384-dimensioni.
2. **Qdrant**: database vettoriale che indicizza vettori e permette ricerche semantiche basate su similarità, supportando filtri sui metadati (payload).
3. **Payload**: contiene titolo, abstract, autori, pub\_date e pmid come dati associati al vettore.
4. **ID punti**: usiamo il `pmid` come ID unico per ogni punto Qdrant.

---

## Perché conservare `pub_date` nel payload?

* La data non entra nell'embedding ma resta utile per:

  * Filtrare ricerche per anno o intervallo temporale
  * Mostrare informazioni temporali nella UI o nei risultati
  * Analisi temporali dei dati

---

## Note importanti

* Assicurati che il campo `pmid` sia sempre convertibile in intero, altrimenti modifica lo script per usare ID stringa o hash.
* Se vuoi scalare oltre localhost, configura correttamente `QDRANT_URL` e la sicurezza API key.
* Puoi estendere il payload con altri metadati a piacimento.

---

## Possibili estensioni

* Preprocessing più avanzato del testo (rimozione stopwords, stemming)
* Aggiunta di campi extra al payload (es. journal, keywords)
* Integrazione con interfacce di ricerca semantica (es. API REST, UI web)
* Automatizzare scraping + caricamento in pipeline

---

Se hai domande o vuoi aiuto per personalizzazioni, chiedimi pure!

---

Ti serve anche un file di esempio JSON o altro?

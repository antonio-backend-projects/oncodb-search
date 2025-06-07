# PubMed Massive Downloader

Questo script permette di scaricare in modo massivo metadati e abstract di articoli scientifici da **PubMed** utilizzando le **NCBI E-Utilities API**.

## Funzionalità

- Ricerca articoli tramite query testuale.
- Scarica fino a 20.000 articoli (configurabile).
- Salvataggio progressivo in formato JSON.
- Possibilità di riprendere lo scraping da un file interrotto.

## Requisiti

- Python 3.7+
- Moduli Python standard: `requests`, `time`, `xml`, `json`, `os`

## Installazione

Clona questo repository o copia il contenuto dello script Python in un file, ad esempio `pubmed_downloader.py`.

Assicurati di avere `requests` installato:

```bash
pip install requests
````

## Utilizzo

Modifica il file Python se vuoi cambiare la query o il numero massimo di articoli. Il punto di partenza è la funzione `main()`:

```python
query = "cancer immunotherapy clinical trial"  # Cambia la query qui
retmax = 20000  # Numero massimo di articoli da scaricare
```

Per eseguire lo script:

```bash
python pubmed_downloader.py
```

Alla fine, troverai un file `pubmed_articles_massive.json` nella stessa directory, contenente i dati degli articoli nel seguente formato:

```json
[
  {
    "title": "Titolo dell'articolo",
    "abstract": "Testo dell'abstract",
    "authors": ["Nome Cognome", "Nome Cognome", ...],
    "pub_date": "2023-11-15",
    "pmid": "12345678"
  },
  ...
]
```

## Raccomandazioni per l'uso responsabile (rate limits)

L'NCBI impone **limiti di utilizzo** per le sue API:

* **3 richieste al secondo** per utenti non autenticati.
* **10 richieste al secondo** se si utilizza un API key personale.

Attualmente lo script inserisce un `sleep` automatico:

* `0.4s` tra chiamate a `esearch`
* `0.5s` tra chiamate a `efetch`
* Retry automatico in caso di errore (5–10s)

### Consigli

* Non ridurre ulteriormente le pause (`time.sleep`) per evitare il ban dell’IP.
* Se hai una **API key NCBI**, puoi aggiungerla ai parametri `params` in entrambi i metodi per aumentare il rate limit (fino a 10 richieste/sec). Vedi [NCBI API Key documentation](https://www.ncbi.nlm.nih.gov/account/settings/).

Esempio per aggiungere l'API key:

```python
params["api_key"] = "YOUR_API_KEY"
```

## Ripresa automatica

Lo script salva progressivamente i risultati nel file JSON. Se eseguito nuovamente, salterà automaticamente i PMIDs già presenti nel file.

Ottieni la API key NCBI (usata per PubMed e altri database NCBI) seguendo questi passi:

1. Vai al sito del **NCBI**:
   [https://www.ncbi.nlm.nih.gov/](https://www.ncbi.nlm.nih.gov/)

2. Se non hai un account, crea un account gratuito NCBI:
   [https://account.ncbi.nlm.nih.gov/signup/](https://account.ncbi.nlm.nih.gov/signup/)

3. Una volta loggato, vai nella tua pagina profilo o direttamente qui:
   [https://www.ncbi.nlm.nih.gov/account/settings/](https://www.ncbi.nlm.nih.gov/account/settings/)

4. Cerca la sezione **API Key Management** o **API Keys**.

5. Clicca su **Create new API key** (o simile).

6. Otterrai una chiave alfanumerica che puoi usare nel tuo script come parametro `api_key`.

---

### Perché serve la API key?

* Aumenta il limite di richieste giornaliere consentite (da 3 richieste al secondo a 10 richieste al secondo).
* Migliora l’affidabilità del tuo scraping.
* Utile se vuoi scaricare tanti dati velocemente.

---

Se vuoi ti posso aiutare a inserire la API key correttamente nel tuo script e mostrarti come usarla nelle chiamate API!


## Licenza

Questo script è fornito "as-is", senza alcuna garanzia. Usalo responsabilmente e nel rispetto delle condizioni d'uso del servizio PubMed.

---

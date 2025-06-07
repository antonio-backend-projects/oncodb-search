import requests
import time
import xml.etree.ElementTree as ET
import json
import os
import argparse
import logging
from datetime import datetime, timedelta

MAX_RETRIES = 5
BATCH_SIZE = 100
MAX_ESARCH_RETMAX = 20000  # limite esearch per singola query

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PubMedDownloader/1.0)"
}


def fetch_pubmed_ids(query, retmax=20000, api_key=None):
    """
    Funzione standard esearch, fino a retmax <= 20000
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    pmids = []
    retstart = 0

    while retstart < retmax:
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": min(BATCH_SIZE, retmax - retstart),
            "retstart": retstart,
            "retmode": "json"
        }
        if api_key:
            params["api_key"] = api_key

        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                response = requests.get(url, params=params, headers=HEADERS)
                response.raise_for_status()
                data = response.json()
                batch_pmids = data["esearchresult"]["idlist"]
                if not batch_pmids:
                    return pmids
                pmids.extend(batch_pmids)
                retstart += len(batch_pmids)
                print(f"✅ Fetched {len(pmids)} PMIDs so far in current chunk...")
                time.sleep(0.4)
                break
            except Exception as e:
                retry_count += 1
                wait_time = min(60, 5 * (2 ** retry_count))
                logging.warning(f"Error fetching PMIDs ({retry_count}/{MAX_RETRIES}): {e}")
                print(f"⚠️ Retry {retry_count}/{MAX_RETRIES} in {wait_time}s...")
                time.sleep(wait_time)
        if retry_count >= MAX_RETRIES:
            logging.error(f"Max retries reached at retstart={retstart}")
            break

    return pmids


def fetch_pubmed_details(pmids, save_path="pubmed_articles.json", api_key=None):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    articles = []

    if os.path.exists(save_path):
        with open(save_path, "r", encoding="utf-8") as f:
            articles = json.load(f)
        already_fetched_pmids = set(a["pmid"] for a in articles)
    else:
        already_fetched_pmids = set()

    for i in range(0, len(pmids), BATCH_SIZE):
        batch_pmids = pmids[i:i + BATCH_SIZE]
        batch_pmids = [pmid for pmid in batch_pmids if pmid not in already_fetched_pmids]
        if not batch_pmids:
            continue

        params = {
            "db": "pubmed",
            "retmode": "xml",
            "id": ",".join(batch_pmids)
        }
        if api_key:
            params["api_key"] = api_key

        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                response = requests.get(url, params=params, headers=HEADERS)
                response.raise_for_status()
                root = ET.fromstring(response.text)

                for article in root.findall(".//PubmedArticle"):
                    art = {}
                    medline = article.find("MedlineCitation")
                    article_data = medline.find("Article")

                    art["title"] = article_data.findtext("ArticleTitle") or ""

                    abstract_text = ""
                    abstract = article_data.find("Abstract")
                    if abstract is not None:
                        abstract_text = " ".join([t.text for t in abstract.findall("AbstractText") if t.text])
                    art["abstract"] = abstract_text

                    authors = []
                    author_list = article_data.find("AuthorList")
                    if author_list is not None:
                        for author in author_list.findall("Author"):
                            last = author.findtext("LastName") or ""
                            first = author.findtext("ForeName") or ""
                            full_name = (first + " " + last).strip()
                            if full_name:
                                authors.append(full_name)
                    art["authors"] = authors

                    pub_date = article_data.find("Journal/JournalIssue/PubDate")
                    year = pub_date.findtext("Year") or ""
                    month = pub_date.findtext("Month") or ""
                    day = pub_date.findtext("Day") or ""
                    art["pub_date"] = f"{year}-{month}-{day}"

                    art["pmid"] = medline.findtext("PMID")

                    articles.append(art)

                logging.info(f"Fetched batch {i // BATCH_SIZE + 1}. Total articles: {len(articles)}")
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(articles, f, ensure_ascii=False, indent=2)
                time.sleep(0.5)
                break
            except Exception as e:
                retry_count += 1
                wait_time = min(60, 5 * (2 ** retry_count))
                logging.warning(f"Error fetching details ({retry_count}/{MAX_RETRIES}): {e}")
                print(f"⚠️ Retry {retry_count}/{MAX_RETRIES} in {wait_time}s...")
                time.sleep(wait_time)

        if retry_count >= MAX_RETRIES:
            logging.error(f"Max retries reached at batch index {i}. Skipping batch.")
            continue

    return articles


def daterange(start_date, end_date, delta_days=30):
    """
    Genera intervalli temporali [start, start+delta_days) fino a end_date
    """
    current = start_date
    while current < end_date:
        yield current, min(current + timedelta(days=delta_days - 1), end_date)
        current += timedelta(days=delta_days)


def fetch_pubmed_ids_over_20000(query, start_year, end_year, api_key=None):
    """
    Suddivide la ricerca in intervalli di tempo per aggirare limite 20k record.
    Usa intervalli di 30 giorni di default (parametrizzabile).
    """
    all_pmids = []

    start_date = datetime(year=start_year, month=1, day=1)
    end_date = datetime(year=end_year, month=12, day=31)

    for (start, end) in daterange(start_date, end_date, delta_days=30):
        # Formatta filtro data in formato PubMed yyyy/mm/dd:yyyy/mm/dd
        date_filter = f'("{start.strftime("%Y/%m/%d")}"[PDAT] : "{end.strftime("%Y/%m/%d")}"[PDAT])'
        combined_query = f"{query} AND {date_filter}"

        print(f"🔍 Fetching PMIDs for interval {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}...")
        logging.info(f"Fetching PMIDs for interval {start} to {end}")

        # Chiediamo quanti risultati ci sono (max 20000)
        count = get_pubmed_count(combined_query, api_key)
        if count == 0:
            continue

        if count > MAX_ESARCH_RETMAX:
            print(f"⚠️ Warning: More than {MAX_ESARCH_RETMAX} results in this interval, consider reducing interval size.")
            logging.warning(f"More than {MAX_ESARCH_RETMAX} results in interval {start} to {end}")

        # Fetch fino a max 20000 in questo intervallo
        pmids = fetch_pubmed_ids(combined_query, retmax=min(count, MAX_ESARCH_RETMAX), api_key=api_key)
        all_pmids.extend(pmids)

    # Rimuove duplicati, se presenti
    unique_pmids = list(set(all_pmids))
    print(f"✅ Total PMIDs fetched overall: {len(unique_pmids)}")
    logging.info(f"Total PMIDs fetched overall: {len(unique_pmids)}")
    return unique_pmids


def get_pubmed_count(query, api_key=None):
    """
    Funzione per ottenere il numero totale di risultati per una query esearch
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": 0
    }
    if api_key:
        params["api_key"] = api_key

    try:
        response = requests.get(url, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        count = int(data["esearchresult"]["count"])
        return count
    except Exception as e:
        logging.error(f"Error getting count for query {query}: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Massive PubMed downloader with over 20k support")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--start_year", type=int, required=True, help="Start year for date partitioning")
    parser.add_argument("--end_year", type=int, required=True, help="End year for date partitioning")
    parser.add_argument("--output", default="pubmed_articles.json", help="Output file path")
    parser.add_argument("--api_key", help="NCBI API key (optional)")
    args = parser.parse_args()

    print(f"🔍 Searching PubMed for: \"{args.query}\" from {args.start_year} to {args.end_year}")
    logging.info(f"Started query: {args.query} from {args.start_year} to {args.end_year}")

    pmids = fetch_pubmed_ids_over_20000(args.query, args.start_year, args.end_year, api_key=args.api_key)
    print(f"📥 Fetched {len(pmids)} PMIDs. Getting article details...")

    articles = fetch_pubmed_details(pmids, save_path=args.output, api_key=args.api_key)
    print(f"✅ Done. Saved {len(articles)} articles to {args.output}")
    logging.info(f"Completed. Saved {len(articles)} articles.")


if __name__ == "__main__":
    main()

import requests
import time
import xml.etree.ElementTree as ET
import json
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PubMedDownloader/1.0)"
}
MAX_RETRIES = 5


def fetch_pubmed_ids(query, retmax=20000):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    pmids = []
    retstart = 0
    batch_size = 100

    while retstart < retmax:
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": min(batch_size, retmax - retstart),
            "retstart": retstart,
            "retmode": "json"
        }

        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                response = requests.get(url, params=params, headers=HEADERS)
                response.raise_for_status()

                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON at retstart={retstart}. Dumping response:")
                    print(response.text[:500])
                    raise e

                batch_pmids = data["esearchresult"]["idlist"]
                if not batch_pmids:
                    print("No more PMIDs found, stopping.")
                    return pmids

                pmids.extend(batch_pmids)
                retstart += len(batch_pmids)
                print(f"✅ Fetched {len(pmids)} PMIDs so far...")
                time.sleep(0.5)
                break
            except Exception as e:
                retry_count += 1
                wait_time = min(60, 5 * (2 ** retry_count))
                print(f"⚠️ Error fetching PMIDs ({retry_count}/{MAX_RETRIES}): {e}. Retrying in {wait_time} sec...")
                time.sleep(wait_time)

        if retry_count >= MAX_RETRIES:
            print(f"❌ Max retries reached at retstart={retstart}. Aborting.")
            break

    return pmids


def fetch_pubmed_details(pmids, save_path="pubmed_articles_massive.json"):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    articles = []
    batch_size = 100

    if os.path.exists(save_path):
        with open(save_path, "r", encoding="utf-8") as f:
            articles = json.load(f)
        already_fetched_pmids = set(a["pmid"] for a in articles)
    else:
        already_fetched_pmids = set()

    for i in range(0, len(pmids), batch_size):
        batch_pmids = pmids[i:i + batch_size]
        batch_pmids = [pmid for pmid in batch_pmids if pmid not in already_fetched_pmids]
        if not batch_pmids:
            continue

        params = {
            "db": "pubmed",
            "retmode": "xml",
            "id": ",".join(batch_pmids)
        }

        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                response = requests.get(url, params=params, headers=HEADERS)
                response.raise_for_status()
                try:
                    root = ET.fromstring(response.text)
                except ET.ParseError as e:
                    print(f"❌ XML parse error. Dumping response:")
                    print(response.text[:500])
                    raise e

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

                print(f"✅ Fetched {len(articles)} articles so far...")
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(articles, f, ensure_ascii=False, indent=2)
                time.sleep(0.5)
                break
            except Exception as e:
                retry_count += 1
                wait_time = min(60, 5 * (2 ** retry_count))
                print(f"⚠️ Error fetching details ({retry_count}/{MAX_RETRIES}): {e}. Retrying in {wait_time} sec...")
                time.sleep(wait_time)

        if retry_count >= MAX_RETRIES:
            print(f"❌ Max retries reached at batch index {i}. Skipping batch.")
            continue

    return articles


def main():
    query = "cancer immunotherapy clinical trial"
    retmax = 10000  # Adjust as needed, max is 20,000 for esearch
    print(f"🔍 Fetching PMIDs for query: \"{query}\" (up to {retmax})...")
    pmids = fetch_pubmed_ids(query, retmax=retmax)
    print(f"📥 Total PMIDs fetched: {len(pmids)}. Downloading article details...")
    articles = fetch_pubmed_details(pmids)
    print(f"✅ Finished. Saved {len(articles)} articles to file.")


if __name__ == "__main__":
    main()

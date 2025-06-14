import pandas as pd
import os
import xml.etree.ElementTree as ET
from urllib.request import urlretrieve
import tarfile
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from tqdm import tqdm
import re

def download_rdf_catalog(url, filename):
    if not os.path.exists(filename):
        print("Downloading RDF catalog (this may take several minutes)...")
        urlretrieve(url, filename)
    else:
        print(f"{filename} already exists, skipping download.")

def extract_rdf_files(tar_filename, extract_dir):
    if not os.path.exists(extract_dir):
        print("Extracting RDF files...")
        with tarfile.open(tar_filename, "r:bz2") as tar:
            tar.extractall(extract_dir)
    else:
        print(f"{extract_dir} already exists, skipping extraction.")

import requests
from bs4 import BeautifulSoup

def parse_rdf_file(rdf_file, ns, public_domain_year):
    try:
        tree = ET.parse(rdf_file)
        root = tree.getroot()

        title = root.find(".//dcterms:title", ns)
        author = root.find(".//pgterms:agent/pgterms:name", ns)

        date_node = root.find(".//dcterms:issued", ns) or root.find(".//dcterms:date", ns)

        year = None
        year_source = "none"
        if date_node is not None and date_node.text:
            match = re.search(r'(\d{4})', date_node.text)
            if match:
                year = int(match.group(1))
                year_source = "issued_date"

        # Step 1: Check metadata flags
        rights_nodes = root.findall(".//pgterms:rights", ns) + root.findall(".//dcterms:rights", ns)
        license_node = root.find(".//pgterms:license", ns)

        public_domain_flag = False
        rights_text_combined = ""

        for node in rights_nodes:
            if node is not None and node.text:
                rights_text_combined += " " + node.text.lower()

        if license_node is not None and license_node.text:
            rights_text_combined += " " + license_node.text.lower()

        if "public domain" in rights_text_combined and "usa" in rights_text_combined:
            public_domain_flag = True

        book_id = os.path.basename(os.path.dirname(rdf_file))

        # Step 2: Fallback scrape if metadata is insufficient
        if not public_domain_flag and (year is None or year > public_domain_year):
            url = f"https://www.gutenberg.org/ebooks/{book_id}"
            try:
                res = requests.get(url, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                rights_div = soup.find('td', string=re.compile(r"copyright status", re.IGNORECASE))
                if rights_div:
                    status = rights_div.find_next_sibling('td')
                    if status and "public domain" in status.text.lower() and "usa" in status.text.lower():
                        public_domain_flag = True
            except Exception as e:
                print(f"⚠️  Error scraping {url}: {e}")

        if parse_rdf_file.counter < 25:
            print(f"DEBUG: {os.path.basename(rdf_file)} → Year: {year} (source: {year_source}), PublicDomainFlag: {public_domain_flag}")

        parse_rdf_file.counter += 1

        if not public_domain_flag and (year is None or year > public_domain_year):
            return None

        if title is None or author is None:
            return None

        formats = root.findall(".//pgterms:file", ns)
        format_urls = []
        for f in formats:
            url = f.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
            if url and not url.endswith('.mp3') and not url.endswith('.m3u'):
                format_urls.append(url)

        return {
            "Title": title.text.strip(),
            "Author": author.text.strip(),
            "Year": year,
            "Year Source": year_source,
            "Public Domain in USA": public_domain_flag,
            "Gutenberg ID": book_id,
            "Formats": ", ".join(format_urls)
        }

    except Exception as e:
        print(f"Error parsing {rdf_file}: {e}")
        return None


parse_rdf_file.counter = 0

def main(output_csv="public_domain_books_full.csv", public_domain_year=1927):
    URL = "https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2"
    RDF_TAR = "rdf-files.tar.bz2"
    EXTRACT_DIR = "rdf-files"

    ns = {
        "dcterms": "http://purl.org/dc/terms/",
        "pgterms": "http://www.gutenberg.org/2009/pgterms/"
    }

    download_rdf_catalog(URL, RDF_TAR)
    extract_rdf_files(RDF_TAR, EXTRACT_DIR)

    rdf_files_pattern = os.path.join(EXTRACT_DIR, "cache", "epub", "*", "*.rdf")
    rdf_files = glob.glob(rdf_files_pattern)

    print(f"Found {len(rdf_files)} RDF files, parsing in parallel...")

    books = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(parse_rdf_file, rdf, ns, public_domain_year): rdf for rdf in rdf_files}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Parsing"):
            result = future.result()
            if result is not None:
                books.append(result)

    print(f"Found {len(books)} public domain books (year <= {public_domain_year} or flagged public domain).")

    df = pd.DataFrame(books)
    df.to_csv(output_csv, index=False)
    print(f"Saved to '{output_csv}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a directory of public domain books from Project Gutenberg RDF catalog.")
    parser.add_argument("--output", type=str, default="public_domain_books_full.csv", help="Output CSV filename")
    parser.add_argument("--year", type=int, default=1927, help="Cutoff year for public domain (inclusive)")
    args = parser.parse_args()

    main(output_csv=args.output, public_domain_year=args.year)

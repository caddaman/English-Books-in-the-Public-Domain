import pandas as pd
import gzip
import os
import xml.etree.ElementTree as ET
from urllib.request import urlretrieve
import tarfile
import glob

# Step 1: Download the RDF catalog
url = "https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2"
filename = "rdf-files.tar.bz2"
if not os.path.exists(filename):
    print("Downloading RDF catalog (may take several minutes)...")
    urlretrieve(url, filename)

# Step 2: Extract the RDF files
if not os.path.exists("rdf-files"):
    print("Extracting RDF files...")
    with tarfile.open(filename, "r:bz2") as tar:
        tar.extractall("rdf-files")

# Step 3: Parse metadata from each RDF file
print("Parsing RDF metadata (this may take a while)...")

books = []
ns = {
    "dcterms": "http://purl.org/dc/terms/",
    "pgterms": "http://www.gutenberg.org/2009/pgterms/"
}

for rdf_file in glob.glob("rdf-files/cache/epub/*/*.rdf"):
    try:
        tree = ET.parse(rdf_file)
        root = tree.getroot()
        
        title = root.find(".//dcterms:title", ns)
        author = root.find(".//pgterms:agent/pgterms:name", ns)
        date = root.find(".//dcterms:issued", ns)
        book_id = os.path.basename(os.path.dirname(rdf_file))

        if title is not None and author is not None:
            year = int(date.text[:4]) if date is not None and date.text[:4].isdigit() else None
            if year and year <= 1927:
                books.append({
                    "Title": title.text.strip(),
                    "Author": author.text.strip(),
                    "Year": year,
                    "Gutenberg ID": book_id
                })
    except Exception as e:
        continue  # skip bad files

# Step 4: Save the results to CSV
print(f"Found {len(books)} public domain books.")
df = pd.DataFrame(books)
df.to_csv("public_domain_books_full.csv", index=False)
print("Saved to 'public_domain_books_full.csv'")

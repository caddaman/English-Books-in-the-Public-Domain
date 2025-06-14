import os
import xml.etree.ElementTree as ET
from pathlib import Path
from tqdm import tqdm
import csv

RDF_DIR = Path("D:/Coding Projects/rdf-files/cache/epub")
CHECKLIST_DIR = Path("checklist_books")
CSV_FILE = "english_public_domain_books.csv"

def is_public_domain(tree):
    for elem in tree.iter():
        if elem.tag.endswith("rights") and elem.text and "public domain" in elem.text.lower():
            return True
    return False

def get_book_info(rdf_path):
    ns = {
        'dcterms': 'http://purl.org/dc/terms/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'pgterms': 'http://www.gutenberg.org/2009/pgterms/',
    }

    try:
        tree = ET.parse(rdf_path)
        root = tree.getroot()

        # Filter to English
        lang = root.find(".//dcterms:language//rdf:Description/rdf:value", ns)
        if lang is None or lang.text.strip().lower() != "en":
            return None

        if not is_public_domain(tree):
            return None

        title = root.find(".//dcterms:title", ns)
        creator = root.find(".//dcterms:creator//pgterms:name", ns)
        book_id = Path(rdf_path).stem.replace("pg", "").replace(".rdf", "")

        return {
            "id": book_id,
            "title": title.text.strip() if title is not None else "Unknown Title",
            "author": creator.text.strip() if creator is not None else "Unknown Author",
        }
    except Exception as e:
        print(f"Failed to parse {rdf_path}: {e}")
        return None

def build_checklist():
    rdf_files = list(RDF_DIR.rglob("*.rdf"))
    print(f"Found {len(rdf_files)} RDF files.")

    checklist = []

    for rdf_path in tqdm(rdf_files, desc="Parsing RDF files"):
        info = get_book_info(rdf_path)
        if info:
            checklist.append(info)

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "author", "completed"])
        writer.writeheader()
        for book in checklist:
            book["completed"] = 0
            writer.writerow(book)

    print(f"Found {len(checklist)} English public domain books. Saved to {CSV_FILE}.")

def show_checklist():
    if not Path(CSV_FILE).exists():
        print("CSV file not found. Run 'build' command first.")
        return

    with open(CSV_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            book_path = CHECKLIST_DIR / f"{row['id']}.txt"
            status = "✅" if book_path.exists() else "❌"
            print(f"[{status}] {row['title']} by {row['author']} (ID: {row['id']})")

def touch_book(book_id):
    CHECKLIST_DIR.mkdir(exist_ok=True)
    book_path = CHECKLIST_DIR / f"{book_id}.txt"
    book_path.touch()
    print(f"Marked book ID {book_id} as completed.")

def delete_book(book_id):
    book_path = CHECKLIST_DIR / f"{book_id}.txt"
    if book_path.exists():
        book_path.unlink()
        print(f"Unmarked book ID {book_id}.")
    else:
        print(f"Book ID {book_id} not found in checklist.")

def search_books(keyword):
    keyword = keyword.lower()
    if not Path(CSV_FILE).exists():
        print("CSV file not found. Run 'build' command first.")
        return

    found = False
    with open(CSV_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if keyword in row['title'].lower() or keyword in row['author'].lower():
                found = True
                book_path = CHECKLIST_DIR / f"{row['id']}.txt"
                status = "✅" if book_path.exists() else "❌"
                print(f"[{status}] {row['title']} by {row['author']} (ID: {row['id']})")
    
    if not found:
        print(f"No results found for '{keyword}'.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python book_checklist.py build         # Build the checklist")
        print("  python book_checklist.py show          # Show checklist status")
        print("  python book_checklist.py mark 12345    # Mark a book as completed")
        print("  python book_checklist.py unmark 12345  # Unmark a book")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "build":
        build_checklist()
    elif cmd == "show":
        show_checklist()
    elif cmd == "mark" and len(sys.argv) == 3:
        touch_book(sys.argv[2])
    elif cmd == "unmark" and len(sys.argv) == 3:
        delete_book(sys.argv[2])
    elif cmd == "search" and len(sys.argv) >= 3:
        keyword = " ".join(sys.argv[2:])
        search_books(keyword)
    else:
        print("Invalid command or missing book ID.")

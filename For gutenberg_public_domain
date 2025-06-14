gutenberg_public_domain.py

# Gutenberg Public Domain Book Scraper

This Python script builds a dataset of public domain books in English from the Project Gutenberg RDF catalog. It's designed for creators, narrators, and enthusiasts who want to explore or work with older texts that are legally free to use in the U.S.

## Features

- Downloads and extracts the official RDF metadata archive from Project Gutenberg.
- Parses each RDF file to extract title, author, year, and available formats.
- Verifies public domain status via metadata and, if needed, by scraping the Project Gutenberg website.
- Saves results to a structured CSV file.
- Multi-threaded parsing for speed.

## Requirements

- Python 3.7+
- Required packages:

```bash
pip install pandas tqdm beautifulsoup4 requests
```

## Usage

Run the script from the command line:

```bash
python gutenberg_scraper.py --output public_domain_books.csv --year 1927
```

**Arguments:**
- `--output`: (optional) Output CSV filename (default: `public_domain_books_full.csv`)
- `--year`: (optional) Latest publication year to include as public domain (default: `1927`)

## Output

The script produces a CSV file with the following columns:

- `Title`: Book title
- `Author`: Author name
- `Year`: Parsed publication year
- `Year Source`: Source of the year value (e.g., `issued_date`)
- `Public Domain in USA`: Whether the book is public domain in the U.S.
- `Gutenberg ID`: Project Gutenberg ID
- `Formats`: Downloadable format URLs

## Sample Output

```csv
Title,Author,Year,Year Source,Public Domain in USA,Gutenberg ID,Formats
The Prince,Niccolò Machiavelli,1513,issued_date,True,12345,https://www.gutenberg.org/ebooks/12345.epub.noimages
```

## Notes

- The initial download and parse may take several minutes.
- A fallback web scrape is used for ambiguous copyright statuses.
- You can adjust the cutoff year using the `--year` argument to match evolving public domain laws.

## License

This project is for educational and personal use. Data comes from [Project Gutenberg](https://www.gutenberg.org), which makes public domain books freely available.


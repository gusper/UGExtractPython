# UG Extract Python

A Python application that scrapes Ultimate Guitar user contribution pages to extract song data and generate markdown lists with Hugo shortcode formatting.

## Features

- **Web Scraping**: Automatically scrapes Ultimate Guitar contribution pages with pagination support
- **HTML File Processing**: Process saved HTML files with wildcard support (e.g., `*.html`)
- **Markdown Generation**: Outputs formatted markdown with Hugo shortcodes for web display
- **Duplicate Detection**: Prevents duplicate entries when processing multiple pages
- **Error Handling**: Robust error handling for network issues and parsing problems

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/UGExtractPython.git
cd UGExtractPython
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Web Scraping (Default)
Scrape all songs from the web:
```bash
python main.py
```

### Process HTML Files
Process saved HTML files:
```bash
python main.py "*.html"
python main.py "page1.html" "page2.html"
```

### Output to File
Redirect output to a markdown file:
```bash
python main.py > songs.md
```

## Output Format

The application generates markdown in this format:

```markdown
107 songs I've transcribed and shared as of August 03, 2025:

* Artist Name - {{<rawhtml>}}<a href="https://tabs.ultimate-guitar.com/tab/..." target="blank">Song Title</a>{{</rawhtml>}} (chords)
```

## Dependencies

- `requests` - HTTP library for web scraping
- `beautifulsoup4` - HTML parsing library

## Architecture

- `main.py` - Entry point with command line argument processing
- `song_scraper.py` - Core scraping and processing logic
- `song.py` - Song data model
- `song_type.py` - File type enumeration (chords, tabs, guitar pro)

## Configuration

The application is currently configured to scrape user ID `6193383-gusp3r` from Ultimate Guitar. To change this, edit the user ID in the `import_web()` method in `song_scraper.py`.

## License

This project is for personal use. Please respect Ultimate Guitar's terms of service and rate limits when using this tool.
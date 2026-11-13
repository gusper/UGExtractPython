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

### Quick Reference
| Goal | Command |
|---|---|
| Update the list (reuses saved view counts, fetches views only for new tabs) | `python main.py > songs.md` |
| Update the list and refresh every view count (a minute or two) | `python main.py --refresh-views > songs.md` |
| Update the list without view counts | `python main.py --no-views > songs.md` |
| See all options | `python main.py --help` |

Then replace the song list on the blog's Music page (`content/music/index.md` in gusper.github.io), from the "songs I've transcribed" line down, with the contents of `songs.md`.

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

### View Counts
Each line includes the tab's total number of views on Ultimate Guitar. Getting a count means visiting that tab's page, so the script saves counts in `view_counts.json` (gitignored) next to `main.py` and reuses them:

- **Default** (`python main.py`): uses saved counts, and fetches views only for tabs that aren't saved yet, such as ones you just posted. Use this for routine list updates.
- **Refresh all** (`python main.py --refresh-views`): fetches every tab's views again and updates the saved counts. That takes a minute or two for ~100 tabs.
- **No views** (`python main.py --no-views`): leaves view counts out of the list.

The first run with no `view_counts.json` fetches every tab, the same as `--refresh-views`. Progress goes to stderr, so it doesn't end up in the markdown output.

### Output to File
Redirect output to a markdown file:
```bash
python main.py > songs.md
```

## Output Format

The application generates markdown in this format:

```markdown
116 songs I've transcribed and shared as of November 20, 2026 (view counts as of November 12, 2026):

* Artist Name - {{<rawhtml>}}<a href="https://tabs.ultimate-guitar.com/tab/..." target="blank">Song Title</a>{{</rawhtml>}} (chords, 6,970 views)
```

The header has two dates because view counts are reused from `view_counts.json` and can be older than the list:

- **List date:** the day you ran the script.
- **View counts date:** the oldest fetch date among the counts shown. A tab fetched today doesn't make the whole list look fresher than it is. Run `--refresh-views` to bring every count, and this date, up to today.

With `--no-views`, the header has no view counts date, and each line ends in just the type, e.g. `(chords)`. A tab whose count couldn't be read also ends in just its type.

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
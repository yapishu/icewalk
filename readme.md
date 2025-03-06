## IceWalk

A concurrent web crawler that outputs content in markdown format for LLMs. It uses Selenium for JavaScript-rendered content and supports depth-limited crawling.

### Features

- Concurrent crawling using ThreadPoolExecutor
- Selenium support for JavaScript-rendered content
- Depth-limited crawling (configurable)
- Extracts metadata (title, description, language)
- Converts HTML to Markdown
- Respects same-domain policy

### Usage
```sh
python3 crawl.py <url> [--max-depth <depth>] [--timeout <seconds>]
```

Options:
- `<url>`: Starting URL for the crawler
- `--max-depth`: Maximum depth for crawling (default: 3, use -1 for unlimited depth)
- `--timeout`: Timeout for each request in seconds (default: 30)

Example:
```
python3 crawl.py https://example.com --max-depth 5 --timeout 45
```


### Output

The crawler generates a single Markdown file named after the domain (e.g., `example.com.md`). Each crawled page is represented as a section in the Markdown file, including:

- Page title
- Source URL
- Language
- Description (if available)
- Main content in Markdown format

### Requirements

- Python 3.x
- Required Python packages: requests, beautifulsoup4, html2text, selenium, webdriver_manager

Install dependencies:
```sh
pip install -r requirements.txt
```

Note: Make sure you have Chrome installed, as the crawler uses ChromeDriver for Selenium.

import requests
from bs4 import BeautifulSoup
import html2text
import json
import sys
from urllib.parse import urlparse, urljoin

def html2markdown(html):
    htmlformatter = html2text.HTML2Text()
    htmlformatter.ignore_links = True
    htmlformatter.ignore_images = True
    htmlformatter.body_width = 0
    return htmlformatter.handle(html)

def fetch_html(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            return response.text
        else:
            print(f"Skipped non-HTML content at {url} (content type: {content_type})")
            return None
    except requests.RequestException as e:
        print(f"Request failed for {url}: {e}")
        return None

def extract_metadata(soup, url):
    title = soup.title.string if soup.title else "No title"
    meta_description = soup.find("meta", attrs={"name": "description"})
    description = meta_description["content"] if meta_description else ""
    language = soup.html.attrs.get('lang', 'unknown')
    return {"title": title, "description": description, "language": language, "sourceURL": url}

def convert_to_json(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    markdown = html2markdown(html)
    metadata = extract_metadata(soup, url)
    return {"content": markdown, "metadata": metadata}

def crawl(url):
    visited = set()
    to_visit = [url]
    results = []

    domain_name = urlparse(url).netloc

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited or current_url.endswith('#'):
            continue

        print(f"Crawling: {current_url}")
        visited.add(current_url)
        html = fetch_html(current_url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link['href']
                parsed_href = urlparse(href)
                if parsed_href.fragment or parsed_href.path.lower().endswith(('.pdf', '.jpg', '.png', '.gif')):
                    continue
                if parsed_href.netloc == domain_name or not parsed_href.netloc:
                    full_url = urljoin(current_url, href)
                    if full_url not in visited:
                        to_visit.append(full_url)

            results.append(convert_to_json(html, current_url))

    return results

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <starting URL>")
        sys.exit(1)

    start_url = sys.argv[1]
    json_output = crawl(start_url)
    print(json.dumps(json_output, indent=4))

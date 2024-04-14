import requests
from bs4 import BeautifulSoup
import html2text
import json
import sys
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import concurrent.futures

def html2markdown(html):
    htmlformatter = html2text.HTML2Text()
    htmlformatter.ignore_links = True
    htmlformatter.ignore_images = True
    htmlformatter.body_width = 0
    return htmlformatter.handle(html)

def fetch_html(url, force_selenium=False):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            html = response.text
            if needs_selenium(html):
                return fetch_with_selenium(url)
            return html
        else:
            print(f"Skipped non-HTML content at {url} (content type: {content_type})")
            return None
    except requests.RequestException as e:
        print(f"Request failed for {url}: {e}")
        return None

def fetch_with_selenium(url):
    options = Options()
    options.headless = True
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    html = driver.page_source
    driver.quit()
    return html

def needs_selenium(html):
    soup = BeautifulSoup(html, 'html.parser')
    script_count = len(soup.find_all('script', {'src': True}))
    return script_count > 5

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
    to_visit = set([url])
    results = []
    domain_name = urlparse(url).netloc
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    futures = {executor.submit(fetch_html, url): url for url in to_visit}

    while futures:
        done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
        for future in done:
            html = future.result()
            if html:
                current_url = futures.pop(future)
                visited.add(current_url)
                print(f"Fetching {current_url}")
                soup = BeautifulSoup(html, 'html.parser')
                results.append(convert_to_json(html, current_url))

                for link in soup.find_all('a', href=True):
                    href = urljoin(current_url, link['href'])
                    parsed_href = urlparse(href)
                    if not parsed_href.fragment and not parsed_href.path.lower().endswith(('.pdf', '.jpg', '.png', '.gif')):
                        if parsed_href.netloc == domain_name and href not in visited:
                            futures[executor.submit(fetch_html, href)] = href

    return results

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <starting URL>")
        sys.exit(1)

    start_url = sys.argv[1]
    domain_name = urlparse(start_url).netloc
    json_output = crawl(start_url)
    
    with open(f"{domain_name}.json", "w") as f:
        f.write(json.dumps(json_output, indent=4))

    print(f"Output written to {domain_name}.json")

import requests
from bs4 import BeautifulSoup
import html2text
import sys
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import concurrent.futures
import time
from requests.exceptions import RequestException, Timeout
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import argparse

def html2markdown(html):
    htmlformatter = html2text.HTML2Text()
    htmlformatter.ignore_links = True
    htmlformatter.ignore_images = True
    htmlformatter.body_width = 0
    return htmlformatter.handle(html)

def fetch_html(url, timeout=30):
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(url)
        
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        time.sleep(5)
        
        html = driver.page_source
        status_code = 200
    except TimeoutException:
        print(f"Timeout error for {url}")
        html = None
        status_code = 408
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        html = None
        status_code = 500
    finally:
        driver.quit()
    
    return html, status_code

def extract_metadata(soup, url):
    title = soup.title.string if soup.title else "No title"
    meta_description = soup.find("meta", attrs={"name": "description"})
    description = meta_description["content"] if meta_description else ""
    language = soup.html.attrs.get('lang', 'unknown') if soup.html and hasattr(soup.html, 'attrs') else 'unknown'
    return title, description, language, url

def convert_to_markdown(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    
    main_content = soup.find('main') or soup.find('body')
    if main_content:
        markdown = html2markdown(str(main_content))
    else:
        markdown = html2markdown(html)
    
    title, description, language, source_url = extract_metadata(soup, url)
    
    md_output = f"# {title}\n\n"
    md_output += f"**URL:** {source_url}\n\n"
    md_output += f"**Language:** {language}\n\n"
    if description:
        md_output += f"**Description:** {description}\n\n"
    md_output += "---\n\n"
    md_output += markdown
    md_output += "\n\n---\n\n"
    
    return md_output

def crawl(url, max_depth=3, timeout=30):
    visited = set()
    to_visit = [(url, 0)]
    results = []
    domain_name = urlparse(url).netloc
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    futures = {}

    start_time = time.time()
    while to_visit:
        new_urls = set()
        current_batch = to_visit[:10]
        to_visit = to_visit[10:]

        print(f"Debug: Processing batch of {len(current_batch)} URLs")

        for current_url, depth in current_batch:
            if current_url not in visited and (max_depth == -1 or depth <= max_depth):
                futures[executor.submit(fetch_html, current_url, timeout=timeout)] = (current_url, depth)

        for future in concurrent.futures.as_completed(futures):
            current_url, depth = futures.pop(future)
            html, status_code = future.result()
            
            print(f"Fetched {current_url} (depth: {depth}, status: {status_code})")
            
            if html and current_url not in visited:
                visited.add(current_url)
                results.append(convert_to_markdown(html, current_url))

                if max_depth == -1 or depth < max_depth:
                    soup = BeautifulSoup(html, 'html.parser')
                    links = soup.find_all('a', href=True)
                    print(f"Debug: Found {len(links)} links on {current_url}")
                    for link in links:
                        href = urljoin(current_url, link['href'])
                        parsed_href = urlparse(href)
                        if (not parsed_href.fragment and 
                            not parsed_href.path.lower().endswith(('.pdf', '.jpg', '.png', '.gif')) and
                            parsed_href.netloc == domain_name and 
                            href not in visited):
                            new_urls.add((href, depth + 1))
                    
                    print(f"Debug: Added {len(new_urls)} new URLs to visit")

        to_visit.extend(new_urls)
        print(f"Debug: Total URLs to visit: {len(to_visit)}")

    executor.shutdown()
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web crawler")
    parser.add_argument("url", help="Starting URL for the crawler")
    parser.add_argument("--max-depth", type=int, default=3, help="Maximum depth for crawling (default: 3, use -1 for unlimited depth)")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for each request in seconds (default: 30)")
    args = parser.parse_args()

    start_url = args.url
    max_depth = args.max_depth
    timeout = args.timeout
    domain_name = urlparse(start_url).netloc

    print(f"Crawling started from {start_url} with max depth {'unlimited' if max_depth == -1 else max_depth}")
    md_output = crawl(start_url, max_depth=max_depth, timeout=timeout)
    print(f"Crawling finished. Total pages crawled: {len(md_output)}")
    
    with open(f"{domain_name}.md", "w", encoding="utf-8") as f:
        f.write("\n\n".join(md_output))

    print(f"Output written to {domain_name}.md")

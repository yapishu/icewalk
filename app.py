from fasthtml.common import *
from crawl import crawl
from urllib.parse import urlparse
import asyncio
from starlette.responses import FileResponse
import os

# pyright: reportUndefinedVariable=false

app, rt = fast_app()

@rt('/')
def get():
    busy_indicator = PicoBusy()
    return Titled("Web Crawler",
        Form(
            Label("URL to crawl:", 
                Input(id="url", name="url", placeholder="Enter URL to crawl", required=True)
            ),
            Label("Max depth:", 
                Input(id="max_depth", name="max_depth", type="number", value="3", min="-1")
            ),
            Label("Timeout (seconds):", 
                Input(id="timeout", name="timeout", type="number", value="30", min="1")
            ),
            Button("Start Crawling", type="submit"),
            action="/crawl",
            method="post",
            hx_post="/crawl",
            hx_target="#result",
            hx_swap="innerHTML"
        ),
        Div(id="result", *busy_indicator)
    )

@rt('/crawl')
async def post(url: str, max_depth: int = 3, timeout: int = 30):
    domain_name = urlparse(url).netloc
    filename = f"{domain_name}.md"
    
    async def run_crawler():
        loop = asyncio.get_event_loop()
        md_output = await loop.run_in_executor(None, crawl, url, max_depth, timeout)
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n\n".join(md_output))
        
        return len(md_output)

    pages_crawled = await run_crawler()
    
    return Div(
        H2("Crawling Complete"),
        P(f"Crawled {pages_crawled} pages from {url}"),
        A("Download Markdown File", href=f"/download/{filename}", download=filename, cls="button")
    )

@rt('/download/{filename}')
def get(filename: str):
    file_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename, media_type='text/markdown')
    else:
        return Div(H2("File Not Found"), P(f"The file {filename} does not exist."))

serve()
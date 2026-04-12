from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

def execute(params):
    query = params.get("query")
    if not query:
        return "Sir, I require a search query to proceed with the research."

    print(f"JARVIS: Researching '{query}' using headless browser...")
    
    try:
        results = DDGS().text(query, max_results=2)
        if not results:
            return "No web results found."
            
        urls = [r['href'] for r in results]
        scraped_texts = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for url in urls:
                try:
                    page.goto(url, timeout=10000)
                    html = page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    text = soup.get_text(separator=' ', strip=True)
                    scraped_texts.append(f"Result from {url}:\n{text[:1500]}")
                except Exception as e:
                    print(f"JARVIS: Failed to fetch {url}: {e}")
                    continue
                    
            browser.close()
            
        if scraped_texts:
            print("JARVIS: Successfully retrieved browser data.")
            return "\n\n".join(scraped_texts)
        else:
            snippets = [r['body'] for r in results]
            return f"Sir, I've conducted the research. Here are the findings:\n\n" + "\n".join(snippets)
            
    except Exception as e:
        print(f"JARVIS: Web search failed: {e}")
        return f"Sir, there was an error during the web research: {e}"
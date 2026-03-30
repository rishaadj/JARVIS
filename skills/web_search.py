from playwright.sync_api import sync_playwright # type: ignore
from bs4 import BeautifulSoup # type: ignore
from duckduckgo_search import DDGS # type: ignore

def execute(params):
    query = params.get("query")
    if not query:
        return "Sir, I require a search query to proceed with the research."

    print(f"JARVIS: Researching '{query}' using headless browser...")
    
    try:
        # Step 1: Search DDG for top URLs
        results = DDGS().text(query, max_results=2)
        if not results:
            return "No web results found."
            
        urls = [r['href'] for r in results]
        scraped_texts = []
        
        # Step 2: Extract text from top URLs using Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for url in urls:
                try:
                    page.goto(url, timeout=10000)
                    # Extract raw text, use BS4 to clean it up
                    html = page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    text = soup.get_text(separator=' ', strip=True)
                    # Truncate to first ~1500 chars to avoid overwhelming the LLM
                    scraped_texts.append(f"Result from {url}:\n{text[:1500]}") # type: ignore
                except Exception as e:
                    print(f"JARVIS: Failed to fetch {url}: {e}")
                    continue
                    
            browser.close()
            
        if scraped_texts:
            print("JARVIS: Successfully retrieved browser data.")
            return "\n\n".join(scraped_texts)
        else:
            # Fallback to pure search snippets if playwright fails
            snippets = [r['body'] for r in results]
            # The instruction provided a return with `summary` which is not defined.
            # Assuming the intent was to rephrase the existing fallback with "Sir,"
            # and keep the original content structure.
            return f"Sir, I've conducted the research. Here are the findings:\n\n" + "\n".join(snippets)
            
    except Exception as e:
        print(f"JARVIS: Web search failed: {e}")
        return f"Sir, there was an error during the web research: {e}"
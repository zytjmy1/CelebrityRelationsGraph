import requests
from bs4 import BeautifulSoup
import re

def get_celebrity_info(name):
    """
    Fetches the Wikipedia page content for a given celebrity name.
    
    Args:
        name (str): The name of the celebrity.
        
    Returns:
        str: The text content of the Wikipedia page, or None if not found.
    """
    # Format the name for the URL (e.g., "Taylor Swift" -> "Taylor_Swift")
    formatted_name = name.replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{formatted_name}"
    
    headers = {
        "User-Agent": "CelebrityGraph/1.0 (https://github.com/yourusername/CelebrityGraph; your-email@example.com)"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            content_div = soup.find(id="mw-content-text")
            
            if content_div:
                paragraphs = content_div.find_all('p')
                text_content = ""
                for p in paragraphs:
                    text_content += p.get_text() + "\n"
                return clean_text(text_content)
        
        # Fallback: DuckDuckGo Search
        print(f"Wikipedia page not found for {name}. Trying Fallback Search...")
        return search_fallback(name)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {name}: {e}")
        return search_fallback(name)

def search_fallback(name):
    """
    Uses DuckDuckGo to find information if Wikipedia fails.
    """
    try:
        from duckduckgo_search import DDGS
        
        query = f"{name} celebrity relationships biography"
        results = DDGS().text(query, max_results=3)
        
        if not results:
            return None
            
        combined_text = ""
        for result in results:
            combined_text += f"{result['title']}\n{result['body']}\n\n"
            
        return f"[FALLBACK SEARCH RESULT]\n{combined_text}"
        
    except ImportError:
        print("duckduckgo-search not installed. Skipping fallback.")
        return None
    except Exception as e:
        print(f"Fallback search error: {e}")
        return None

def clean_text(text):
    """
    Cleans the text by removing references (e.g., [1]) and extra whitespace.
    """
    # Remove citation references like [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

if __name__ == "__main__":
    # Simple test
    name = "Taylor Swift"
    print(f"Fetching info for {name}...")
    info = get_celebrity_info(name)
    if info:
        print(f"Successfully fetched {len(info)} characters.")
        print(f"Preview: {info[:200]}...")
    else:
        print("Failed to fetch info.")

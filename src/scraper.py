"""Scraper for NOS.nl homepage."""
import requests
from bs4 import BeautifulSoup
import os


def scrape_nos_articles(max_articles: int = 10) -> list[dict]:
    """Scrape article titles and descriptions from NOS.nl homepage.
    
    Args:
        max_articles: Maximum number of articles to scrape
        
    Returns:
        List of dicts with 'title', 'description', and 'url'
    """
    base_url = os.getenv('NOS_BASE_URL', 'https://nos.nl')
    
    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            )
        }
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {base_url}: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []
    
    # NOS.nl uses article elements, adjust selector as needed
    article_elements = soup.find_all('article', limit=max_articles)
    
    for element in article_elements:
        try:
            title_elem = element.find('h2') or element.find('h3')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            desc_elem = element.find('p')
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            link_elem = element.find('a', href=True)
            url = link_elem['href'] if link_elem else None
            
            if title and description:
                articles.append({
                    'title': title,
                    'description': description,
                    'url': url,
                })
        except Exception as e:
            print(f"Error parsing article element: {e}")
            continue
    
    return articles

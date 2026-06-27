"""Sentiment analysis using Ollama."""
import requests
import os
from typing import Literal


def analyze_sentiment(title: str, description: str) -> Literal['POSITIVE', 'NEGATIVE']:
    """Analyze sentiment of an article using Ollama.
    
    Args:
        title: Article title
        description: Article description
        
    Returns:
        'POSITIVE' or 'NEGATIVE'
    """
    ollama_host = os.getenv(
        'OLLAMA_HOST',
        'http://ollama-lb.gobble.svc.cluster.local:11434'
    )
    model = os.getenv('SENTIMENT_MODEL', 'llama3.2:1b')
    
    prompt = (
        f"Analyze the sentiment of this news article. "
        f"Reply with ONLY 'POSITIVE' or 'NEGATIVE'.\n\n"
        f"Title: {title}\n"
        f"Description: {description}"
    )
    
    try:
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        
        result = response.json()
        sentiment_text = result.get('response', '').strip().upper()
        
        if 'POSITIVE' in sentiment_text:
            return 'POSITIVE'
        elif 'NEGATIVE' in sentiment_text:
            return 'NEGATIVE'
        else:
            # Default to NEGATIVE if unclear
            print(f"Unclear sentiment response: {sentiment_text}")
            return 'NEGATIVE'
    except requests.RequestException as e:
        print(f"Error querying Ollama: {e}")
        return 'NEGATIVE'

"""Scraper for NOS.nl using RSS Feeds.

===================================

This module provides functionality to extract article metadata from the official
NOS RSS streams based on specific news categories, bypassing fragile HTML scraping
patterns and cleansing text payloads for down-stream SLM ingestion.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Dict, List
import requests

# Importeer de feed-configuratie en types uit je sentiment-module
from src.sentiment import NOS_RSS_FEEDS, NEWS_CATEGORY


class HTMLTagStripper(HTMLParser):
    """A simple parser to extract raw text data from strings containing HTML tags."""

    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self) -> str:
        return "".join(self.fed)


def strip_html_tags(html_content: str) -> str:
    """Strip HTML tags from a string, returning only the text content.

    :param html_content: The raw string containing HTML markup elements.
    :type html_content: str
    :return: Cleansed plaintext string.
    :rtype: str
    """
    if not html_content:
        return ""
    stripper = HTMLTagStripper()
    stripper.feed(html_content)
    return stripper.get_data().strip()


def scrape_nos_articles(
    category: NEWS_CATEGORY = "VOORPAGINA", max_articles: int = 3
) -> List[Dict[str, str]]:
    """Fetch article titles, descriptions, and URLs from a specific NOS RSS feed.

    :param category: The target NOS section (e.g., 'SPORT', 'POLITIEK').
        Defaults to 'VOORPAGINA'.
    :type category: NEWS_CATEGORY
    :param max_articles: Maximum number of articles to extract from the stream,
        defaults to 3.
    :type max_articles: int, optional
    :return: A list of dictionaries containing structured, text-cleansed article nodes.
    :rtype: List[Dict[str, str]]
    """
    # Haal de dynamische URL op op basis van de meegegeven categorie
    rss_url = NOS_RSS_FEEDS.get(category, None)
    print(f"Fetching articles from [{category}] RSS feed: {rss_url}")

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            )
        }
        response = requests.get(rss_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Network error targeting context endpoint [{category}]: {e}")
        return []

    articles = []

    try:
        root = ET.fromstring(response.content)
        items = root.findall(".//item")[:max_articles]

        for item in items:
            title_node = item.find("title")
            desc_node = item.find("description")
            url_node = item.find("link")

            title = title_node.text.strip() if title_node is not None else ""
            raw_description = (
                desc_node.text.strip() if desc_node is not None else ""
            )
            url = url_node.text.strip() if url_node is not None else ""

            # Run the description payload through the HTML text filter
            cleaned_description = strip_html_tags(raw_description)

            if title:
                articles.append(
                    {
                        "title": title,
                        "description": cleaned_description,
                        "url": url,
                        "category": category,
                    }
                )

    except ET.ParseError as e:
        print(f"XML Tree parsing crash for category [{category}]: {e}")

    return articles


if __name__ == "__main__":
    # Test-run om te zien of het schakelen tussen feeds goed gaat
    for cat in ["VOORPAGINA", "SPORT", "POLITIEK"]:
        print(f"\n--- SCRAPING CATEGORY: {cat} ---")
        news_items = scrape_nos_articles(category=cat, max_articles=2)
        for idx, item in enumerate(news_items, 1):
            print(f"  [{idx}] {item['title']} (Cat: {item['category']})")

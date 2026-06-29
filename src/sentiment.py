"""Sentiment analysis using Ollama.

This module sends NOS article text to Ollama and maps the returned score to a
trinary sentiment label for the DAG, split by news category.
"""

from __future__ import annotations

import os
from typing import Literal

import requests

DEFAULT_OLLAMA_HOST = "http://ollama-lb.gobble.svc.cluster.local:11434"
DEFAULT_SENTIMENT_MODEL = "gemma2:2b"

# Beschikbare categorieën op NOS.nl via hun RSS-structuur
NEWS_CATEGORY = Literal[
    "VOORPAGINA",
    "BINNENLAND",
    "BUITENLAND",
    "POLITIEK",
    "ECONOMIE",
    "SPORT",
    "REGIONAAL",
]

SentimentLabel = Literal["POSITIVE", "NEGATIVE", "NEUTRAL"]

# De officiële RSS feed URL's van de NOS
NOS_RSS_FEEDS: dict[NEWS_CATEGORY, str] = {
    "VOORPAGINA": "https://feeds.nos.nl/nosnieuwsalgemeen",
    "BINNENLAND": "https://feeds.nos.nl/nosnieuwsbinnenland",
    "BUITENLAND": "https://feeds.nos.nl/nosnieuwsbuitenland",
    "POLITIEK": "https://feeds.nos.nl/nosnieuwspolitiek",
    "ECONOMIE": "https://feeds.nos.nl/nosnieuwseconomie",
    "SPORT": "https://feeds.nos.nl/nossportalgemeen",
}


def analyze_sentiment(
    title: str, category: NEWS_CATEGORY = "VOORPAGINA"
) -> SentimentLabel | None:
    """Analyze the sentiment of an article using ONLY the title and category context.

    :param title: Article title.
    :type title: str
    :param category: The NOS section the article belongs to.
    :type category: NEWS_CATEGORY
    :returns: ``POSITIVE``, ``NEGATIVE``, ``NEUTRAL`` or ``None`` on failure.
    :rtype: SentimentLabel | None
    """
    ollama_host = os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    model = os.getenv("SENTIMENT_MODEL", DEFAULT_SENTIMENT_MODEL)

    print(
        f"Querying Ollama ({model}) for category [{category}] | Title: {title}"
    )

    # Door de categorie mee te geven, snapt de iGPU/LLM de context nóg beter
    system_message = (
        "Je bent een kille, objectieve data-parser. Je classificeert de emotionele impact van een nieuwskop.\n"
        f"De huidige kop komt uit de categorie: {category}.\n\n"
        "Kies ALTIJD uit exact één van deze drie labels:\n"
        "- NEGATIVE: Expliciet negatieve gebeurtenissen zoals menselijk leed, misdaad, moord, ongelukken, deportaties, hinder, oorlog, grote crisissen of zware schandalen.\n"
        "- POSITIVE: Expliciet positieve gebeurtenissen zoals sportoverwinningen, feestelijkheden, grote successen, vrolijk nieuws, blijdschap of mooie doorbraken.\n"
        "- NEUTRAL: Al het overige nieuws. Denk aan algemene politieke plannen, zakelijke updates, economische verschuivingen, droge maatschappelijke ontwikkelingen, of media-aankondigingen.\n\n"
        "Regels:\n"
        "1. Antwoord met exact één woord: POSITIVE, NEGATIVE of NEUTRAL\n"
        "2. Geef GEEN uitleg, GEEN introductie, GEEN interpunctie.\n"
        "3. Als de kop puur feitelijk, zakelijk of informatief is zonder duidelijke tragedie of feest, kies dan ALTIJD NEUTRAL."
    )

    user_message = f"Nieuwskop: {title}"

    try:
        response = requests.post(
            f"{ollama_host}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 5,
                },
            },
            timeout=60,
        )
        response.raise_for_status()

        result = response.json()
        message_content = (
            result.get("message", {}).get("content", "").strip().upper()
        )

        if "POSITIVE" in message_content:
            return "POSITIVE"
        if "NEGATIVE" in message_content:
            return "NEGATIVE"
        if "NEUTRAL" in message_content:
            return "NEUTRAL"

        print(
            f"Model did not return a valid label. Raw output: {message_content}"
        )
        return None

    except requests.RequestException as exc:
        print(f"Error querying Ollama sentiment: {exc}")
        return None


def get_rss_url(category: NEWS_CATEGORY) -> str:
    """Get the official NOS RSS URL for a given category.

    :param category: The desired news category.
    :type category: NEWS_CATEGORY
    :returns: The RSS feed URL string.
    :rtype: str
    """
    return NOS_RSS_FEEDS.get(category, NOS_RSS_FEEDS["VOORPAGINA"])

"""Sentiment analysis using Ollama.

This module sends NOS article text to Ollama and maps the returned score to a
trinary sentiment label for the DAG.
"""

from __future__ import annotations

import os
from typing import Literal

import requests

DEFAULT_OLLAMA_HOST = "http://ollama-lb.gobble.svc.cluster.local:11434"
DEFAULT_SENTIMENT_MODEL = "gemma2:2b"

# Uitgebreid met NEUTRAL
SentimentLabel = Literal["POSITIVE", "NEGATIVE", "NEUTRAL"]


def analyze_sentiment(title: str, description: str) -> SentimentLabel | None:
    """Analyze the sentiment of an article using ONLY the title.

    :param title: Article title.
    :type title: str
    :param description: Article description (ignored to reduce noise).
    :type description: str
    :returns: ``POSITIVE``, ``NEGATIVE``, ``NEUTRAL`` or ``None`` on failure.
    :rtype: SentimentLabel | None
    """
    ollama_host = os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    model = os.getenv("SENTIMENT_MODEL", DEFAULT_SENTIMENT_MODEL)

    print(
        f"Querying Ollama at {ollama_host} with chat model {model} (Title only)..."
    )

    system_message = (
        "Je bent een kille, objectieve data-parser. Je classificeert de emotionele impact van een nieuwskop.\n\n"
        "Kies ALTIJD uit exact één van deze drie labels:\n"
        "- NEGATIVE: Expliciet negatieve gebeurtenissen zoals menselijk leed, misdaad, moord, ongelukken, deportaties, oorlog, grote crisissen of zware schandalen.\n"
        "- POSITIVE: Expliciet positieve gebeurtenissen zoals sportoverwinningen, feestelijkheden, grote successen, vrolijk nieuws of mooie doorbraken.\n"
        "- NEUTRAL: Al het overige nieuws. Denk aan algemene politieke plannen, zakelijke updates, economische verschuivingen, droge maatschappelijke ontwikkelingen (zoals stroomnetten of defensiekoersen), of media-aankondigingen.\n\n"
        "Regels:\n"
        "1. Antwoord met exact één woord: POSITIVE, NEGATIVE of NEUTRAL\n"
        "2. Geef GEEN uitleg, GEEN introductie, GEEN interpunctie.\n"
        "3. Als de kop puur feitelijk, zakelijk of informatief is zonder duidelijke tragedie of feest, kies dan ALTIJD NEUTRAL."
    )

    # We sturen nu ALLEEN de titel mee om ruis uit de beschrijving te voorkomen
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

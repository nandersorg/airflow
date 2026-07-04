"""Persistence helpers for storing analyzed news sentiment rows."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any

import psycopg2


def get_results_database_url() -> str | None:
    """Return the analytics database URL if one is configured."""
    return os.getenv("RESULTS_DATABASE_URL") or os.getenv(
        "ML_PLATFORM_DATABASE_URL"
    )


def persist_article_sentiment(article: dict[str, Any]) -> None:
    """Upsert a single analyzed article into the shared PostgreSQL store."""
    database_url = get_results_database_url()
    if not database_url:
        print(
            "Skipping sentiment persistence: RESULTS_DATABASE_URL not configured."
        )
        return

    if not article.get("url"):
        print("Skipping sentiment persistence: article has no URL.")
        return

    scraped_at = article.get("scraped_at") or datetime.now(timezone.utc)
    published_at = article.get("published_at")
    analyzed_at = article.get("analyzed_at") or datetime.now(timezone.utc)

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO news_articles (
                    source,
                    category,
                    title,
                    description,
                    url,
                    sentiment,
                    published_at,
                    scraped_at,
                    analyzed_at,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (url) DO UPDATE
                SET source = EXCLUDED.source,
                    category = EXCLUDED.category,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    sentiment = EXCLUDED.sentiment,
                    published_at = EXCLUDED.published_at,
                    scraped_at = EXCLUDED.scraped_at,
                    analyzed_at = EXCLUDED.analyzed_at,
                    updated_at = NOW()
                """,
                (
                    article.get("source", "NOS"),
                    article["category"],
                    article["title"],
                    article.get("description"),
                    article["url"],
                    article["sentiment"],
                    published_at,
                    scraped_at,
                    analyzed_at,
                ),
            )

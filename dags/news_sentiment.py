from datetime import datetime, timedelta, timezone

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scraper import scrape_nos_articles
from src.sentiment import analyze_sentiment, NOS_RSS_FEEDS
from src.storage import persist_article_sentiment

default_args = {
    "owner": "nander",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 6, 27, tzinfo=timezone.utc),
}

dag = DAG(
    "news_sentiment",
    default_args=default_args,
    description="Scrape NOS.nl and analyze article sentiment via Ollama",
    schedule="0 6 * * *",  # 06:00 UTC daily
    catchup=False,
)


def scrape_and_analyze(**context):
    """Scrape NOS articles and run sentiment analysis."""
    articles = []
    for feed in NOS_RSS_FEEDS:
        new_articles = scrape_nos_articles(category=feed, max_articles=10)
        articles.extend(new_articles)

    results = []
    for article in articles:
        sentiment = analyze_sentiment(
            article["title"], category=article["category"]
        )
        analyzed_at = datetime.now(timezone.utc)
        result = {
            **article,
            "sentiment": sentiment,
            "analyzed_at": analyzed_at,
            "timestamp": analyzed_at.isoformat(),
        }
        results.append(result)
        print(f"  {article['title'][:60]}... → {sentiment}")

        if sentiment is None:
            print(
                f"  Skipping persistence for article without sentiment: {article['title'][:60]}..."
            )
            continue

        persist_article_sentiment(result)

    print(f"Completed sentiment analysis for {len(results)} articles")


scrape_task = PythonOperator(
    task_id="scrape_and_analyze",
    python_callable=scrape_and_analyze,
    do_xcom_push=False,
    dag=dag,
)

scrape_task

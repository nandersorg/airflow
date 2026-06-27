from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.scraper import scrape_nos_articles
from src.sentiment import analyze_sentiment

default_args = {
    "owner": "nander",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 6, 27),
}

dag = DAG(
    "news_sentiment",
    default_args=default_args,
    description="Scrape NOS.nl and analyze article sentiment via Ollama",
    schedule_interval="0 6 * * *",  # 06:00 UTC daily
    catchup=False,
)


def scrape_and_analyze(**context):
    """Scrape NOS articles and run sentiment analysis."""
    articles = scrape_nos_articles()
    print(f"Scraped {len(articles)} articles from NOS.nl")

    results = []
    for article in articles:
        sentiment = analyze_sentiment(article["title"], article["description"])
        result = {
            **article,
            "sentiment": sentiment,
            "timestamp": datetime.utcnow().isoformat(),
        }
        results.append(result)
        print(f"  {article['title'][:60]}... → {sentiment}")

    # Store results in XCom for downstream tasks
    context["task_instance"].xcom_push(key="sentiment_results", value=results)
    return results


scrape_task = PythonOperator(
    task_id="scrape_and_analyze",
    python_callable=scrape_and_analyze,
    dag=dag,
)

scrape_task

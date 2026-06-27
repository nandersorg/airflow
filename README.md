# Airflow Pipelines

Apache Airflow orchestration for ML and data pipelines, running on MicroK8s with shared Ollama service.

## Structure

- `dags/` — Airflow DAG definitions
- `src/` — Reusable Python modules (scrapers, analyzers, etc.)
- `k8s/` — Kubernetes manifests for Airflow deployment
- `docker/` — Custom Airflow image definition

## Quick Start

### Local development

```bash
pip install -r requirements.txt
export AIRFLOW_HOME=$PWD
airflow db init
airflow webserver -p 8080
airflow scheduler
```

Then open http://localhost:8080

### Deploy to MicroK8s

```bash
microk8s kubectl apply -f k8s/namespace.yaml
microk8s kubectl apply -f k8s/airflow.yaml
```

## DAGs

### `news_sentiment`

Scrapes NOS.nl homepage, extracts article titles and descriptions, and runs sentiment analysis via the Ollama service in the `gobble` namespace.

Schedule: Daily at 06:00 UTC

**Dependencies:**
- `requests` — HTTP requests
- `beautifulsoup4` — HTML parsing
- Running Ollama service at `http://ollama-lb.gobble.svc.cluster.local:11434`

## Configuration

See `.env.example` for required environment variables.

## Pre-commit hooks

```bash
pre-commit install
pre-commit run --all-files
```

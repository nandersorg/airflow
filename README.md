# Airflow Pipelines

Apache Airflow orchestration for ML and data pipelines, running on MicroK8s with shared Ollama service.

## ⚠️ Security Setup (REQUIRED for Public Repo)

Before deploying, you **must** add these secrets to your GitHub repository:

### GitHub Repository Secrets

Navigate to **Settings → Secrets and variables → Actions** and add:

| Secret Name | Description | Example |
|---|---|---|
| `AIRFLOW_DATABASE_URL` | Database connection string | `sqlite:////home/airflow/airflow.db` or `postgresql://airflow:password@postgres.postgresql.svc.cluster.local:5432/postgres` |

**For SQLite (development):**
```
sqlite:////home/airflow/airflow.db
```

**For PostgreSQL (production):**
```
postgresql://airflow:<password>@postgres.postgresql.svc.cluster.local:5432/postgres
```

See PostgreSQL repo for shared database setup.

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
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:////$(pwd)/airflow.db
airflow db init
airflow webserver -p 8080
airflow scheduler
```

Then open http://localhost:8080

### Deploy to MicroK8s

1. **Add `AIRFLOW_DATABASE_URL` secret to GitHub** (see Security Setup above)

2. **Deploy via GitHub Actions:**
   ```bash
   git push origin main
   # or manually trigger from GitHub UI: Actions → Deploy Airflow → Run workflow
   ```

3. **Or deploy manually:**
   ```bash
   microk8s kubectl apply -f k8s/namespace.yaml

   # Create secret
   microk8s kubectl create secret generic airflow-secret \
     --from-literal=DATABASE_URL="sqlite:////home/airflow/airflow.db" \
     --namespace=airflow

   # Apply deployment
   microk8s kubectl apply -f k8s/airflow.yaml
   ```

4. **Access Airflow:**
   ```bash
   microk8s kubectl port-forward -n airflow svc/airflow-webserver 8080:8080
   # Open http://localhost:8080
   ```

## DAGs

### `news_sentiment`

Scrapes NOS.nl RSS feed, extracts article titles and descriptions, and runs sentiment analysis via the Ollama service in the `gobble` namespace.

Schedule: Daily at 06:00 UTC

**Dependencies:**
- `requests` — HTTP requests
- `beautifulsoup4` — RSS/HTML parsing
- Running Ollama service at `http://ollama-lb.gobble.svc.cluster.local:11434`

## Configuration

### Environment Variables

All configuration uses environment variables (no hardcoded values):

```bash
# Airflow
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN   # Database connection (from secret)
AIRFLOW__CORE__DAGS_FOLDER            # DAGs location
AIRFLOW__CORE__LOAD_EXAMPLES          # Load example DAGs

# Ollama
OLLAMA_HOST                           # Ollama service address

# News Sentiment
NOS_BASE_URL                          # NOS.nl URL (default: https://nos.nl)
SENTIMENT_MODEL                       # Ollama model (default: llama3.2:1b)
```

Local development: See `.env.example` for template.

## Pre-commit hooks

```bash
pre-commit install
pre-commit run --all-files
```

Validates YAML syntax and prevents secret commits.

```bash
pre-commit install
pre-commit run --all-files
```

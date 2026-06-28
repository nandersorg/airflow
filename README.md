# Airflow Pipelines

Apache Airflow orchestration for ML and data pipelines, running on MicroK8s with shared Ollama service.

## ⚠️ Security Setup (REQUIRED for Public Repo)

Before deploying, you **must** add these secrets to your GitHub repository:

### GitHub Repository Secrets

Navigate to **Settings → Secrets and variables → Actions** and add:

| Secret Name | Description | Example |
|---|---|---|
| `AIRFLOW_DATABASE_URL` | Database connection string | Use PostgreSQL for Kubernetes: `postgresql://airflow:password@postgres.postgresql.svc.cluster.local:5432/postgres` |
| `AIRFLOW_ADMIN_USERNAME` | Airflow UI admin username | `admin` |
| `AIRFLOW_ADMIN_PASSWORD` | Airflow UI admin password | A strong random password |

The deploy job also installs `apache-airflow-providers-fab`, which is required for the Airflow `users` CLI commands used to bootstrap the UI login.

**For SQLite (local development only):**
```
sqlite:////home/airflow/airflow.db
```

**For PostgreSQL (GitHub Actions / Kubernetes):**
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
airflow db migrate
airflow api-server -p 3003
airflow scheduler
airflow dag-processor
```

Then open http://localhost:3003

### Deploy to MicroK8s

1. **Add `AIRFLOW_DATABASE_URL`, `AIRFLOW_ADMIN_USERNAME`, and `AIRFLOW_ADMIN_PASSWORD` secrets to GitHub** (see Security Setup above)

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
       --from-literal=DATABASE_URL="postgresql://airflow:<password>@postgres.postgresql.svc.cluster.local:5432/postgres" \
       --namespace=airflow

    # Create admin user secret
    microk8s kubectl create secret generic airflow-admin-secret \
       --from-literal=USERNAME="admin" \
       --from-literal=PASSWORD="<strong-password>" \
       --namespace=airflow

    # Apply the migration job first, then the workloads
    microk8s kubectl apply -f k8s/db-migrate.yaml
    microk8s kubectl wait --for=condition=complete job/airflow-db-migrate -n airflow --timeout=10m
    microk8s kubectl apply -f k8s/admin-user.yaml
    microk8s kubectl wait --for=condition=complete job/airflow-admin-bootstrap -n airflow --timeout=10m
    microk8s kubectl apply -f k8s/airflow.yaml -f k8s/scheduler.yaml -f k8s/dag-processor.yaml
   ```

4. **Access Airflow:**
   ```bash
   microk8s kubectl port-forward -n airflow svc/airflow-webserver 3003:3003
   # Open http://localhost:3003
   ```

## DAGs

### `news_sentiment`

Scrapes NOS.nl RSS feed, extracts article titles and descriptions, and runs sentiment analysis via the Ollama service in the `gobble` namespace.

Schedule: Daily at 06:00 UTC

**Dependencies:**
- `requests` — HTTP requests
- `beautifulsoup4` — RSS/HTML parsing
- `psycopg2-binary` — PostgreSQL driver for metadata DB
- `asyncpg` — async PostgreSQL driver used by Airflow 3
- Running Ollama service at `http://ollama-lb.gobble.svc.cluster.local:11434`

## Configuration

### Environment Variables

All configuration uses environment variables (no hardcoded values):

```bash
# Airflow
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN   # Database connection (from secret)
AIRFLOW__CORE__DAGS_FOLDER            # DAGs location
AIRFLOW__CORE__LOAD_EXAMPLES          # Load example DAGs
AIRFLOW__CORE__EXECUTOR               # Executor (LocalExecutor)

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

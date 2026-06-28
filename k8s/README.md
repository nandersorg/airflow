## Airflow Kubernetes Deployment

### Files

- `namespace.yaml` — Airflow namespace
- `airflow.yaml` — Airflow api-server deployment, service, and PVC
- `airflow.yaml` — Airflow api-server deployment, service, and configmap-backed DAG mounts
- `scheduler.yaml` — Airflow scheduler deployment
- `dag-processor.yaml` — Airflow DAG processor deployment
- `db-migrate.yaml` — metadata database migration job

The deploy workflow creates `airflow-dags` and `airflow-src` configmaps from the checked-in DAGs and local modules.

### Quick start

```bash
cd /home/nander/repos/airflow

# Apply manifests
microk8s kubectl apply -f k8s/namespace.yaml
microk8s kubectl apply -f k8s/db-migrate.yaml
microk8s kubectl wait --for=condition=complete job/airflow-db-migrate -n airflow --timeout=10m
microk8s kubectl wait --for=condition=complete job/airflow-admin-bootstrap -n airflow --timeout=10m
microk8s kubectl apply -f k8s/airflow.yaml -f k8s/scheduler.yaml -f k8s/dag-processor.yaml

# Check status
microk8s kubectl get pods -n airflow
microk8s kubectl get svc -n airflow

# Access api-server
microk8s kubectl port-forward -n airflow svc/airflow-webserver 3003:3003
```

Then open http://localhost:3003

### Notes

- api-server uses `LocalExecutor` (single-machine)
- Database uses PostgreSQL in Kubernetes; SQLite only for local single-process development
- DAGs and local helper modules mounted from configmaps created by the deploy workflow
- Ollama service accessed at `http://ollama-lb.gobble.svc.cluster.local:11434`

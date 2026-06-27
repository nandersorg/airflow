## Airflow Kubernetes Deployment

### Files

- `namespace.yaml` — Airflow namespace
- `airflow.yaml` — Airflow webserver deployment, service, ConfigMap, and PVC
- `scheduler.yaml` — Airflow scheduler job (optional, for DAG scheduling)

### Quick start

```bash
cd /home/nander/repos/airflow

# Apply manifests
microk8s kubectl apply -f k8s/namespace.yaml
microk8s kubectl apply -f k8s/airflow.yaml

# Check status
microk8s kubectl get pods -n airflow
microk8s kubectl get svc -n airflow

# Access webserver
microk8s kubectl port-forward -n airflow svc/airflow-webserver 8080:8080
```

Then open http://localhost:8080

### Notes

- Webserver uses `LocalExecutor` (single-machine)
- Database uses SQLite (for dev; use PostgreSQL in production)
- DAGs mounted via PVC from hostpath storage
- Ollama service accessed at `http://ollama-lb.gobble.svc.cluster.local:11434`

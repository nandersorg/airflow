import datetime
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import (
    KubernetesPodOperator,
)
from kubernetes.client import models as k8s

default_args = {
    "owner": "nander",
    "start_date": datetime.datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}

# Mount your cluster's MinIO secrets to provide storage backend access
minio_secret_env = [
    k8s.V1EnvVar(
        name="MINIO_ROOT_USER",
        value_from=k8s.V1EnvVarSource(
            secret_key_ref=k8s.V1SecretKeySelector(
                name="mlflow-minio-secret", key="MINIO_ROOT_USER"
            )
        ),
    ),
    k8s.V1EnvVar(
        name="MINIO_ROOT_PASSWORD",
        value_from=k8s.V1EnvVarSource(
            secret_key_ref=k8s.V1SecretKeySelector(
                name="mlflow-minio-secret", key="MINIO_ROOT_PASSWORD"
            )
        ),
    ),
]

with DAG(
    "quickdraw_weekly_retrain",
    default_args=default_args,
    schedule_interval="@weekly",
    catchup=False,
    tags=["mlops", "quickdraw"],
) as dag:
    """
    Weekly automated retraining pipeline orchestrating isolation workloads
    within the ml-serving namespace on MicroK8s.
    """

    # Cluster internal DNS endpoints to route traffic without leaving the node
    mlflow_uri = "http://mlflow-service.gobble.svc.cluster.local:5000"
    minio_uri = "http://minio-service.gobble.svc.cluster.local:9000"

    run_quickdraw_training = KubernetesPodOperator(
        task_id="run_quickdraw_training",
        name="quickdraw-training-worker",
        namespace="ml-serving",
        # Pulls the stable training target built by GitHub Actions
        image="localhost:32000/quickdraw-training:latest",
        cmds=["python", "train.py"],
        # Strict resource boundaries to prevent host RAM/Swap starvation
        container_resources=k8s.V1ResourceRequirements(
            requests={"memory": "1Gi", "cpu": "1"},
            limits={"memory": "4Gi", "cpu": "2"},
        ),
        env_vars=[
            k8s.V1EnvVar(name="MLFLOW_TRACKING_URI", value=mlflow_uri),
            k8s.V1EnvVar(name="MLFLOW_S3_ENDPOINT_URL", value=minio_uri),
            k8s.V1EnvVar(name="PYTHONUNBUFFERED", value="1"),
            *minio_secret_env,
        ],
        is_delete_operator_pod=True,
        in_cluster=True,
        get_logs=True,
    )

    run_quickdraw_training

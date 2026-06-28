from datetime import datetime, timedelta, timezone

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG


def smoke_test() -> None:
    """Run a local-only smoke test."""
    print("Airflow smoke test is running")
    print(f"Current UTC time: {datetime.now(timezone.utc).isoformat()}")


default_args = {
    "owner": "nander",
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
    "start_date": datetime(2026, 6, 28, tzinfo=timezone.utc),
}

with DAG(
    "airflow_smoke_test",
    default_args=default_args,
    description="Minimal no-network DAG to validate Airflow task execution",
    schedule=None,
    catchup=False,
) as dag:
    smoke_task = PythonOperator(
        task_id="smoke_test",
        python_callable=smoke_test,
        do_xcom_push=False,
    )

    smoke_task

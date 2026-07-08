FROM apache/airflow:3.2.2-python3.11

# Copy your requirements definition file
COPY --chown=airflow:root requirements.txt /requirements.txt

# Install packages into the container layer
RUN pip install --no-cache-dir --user -r /requirements.txt

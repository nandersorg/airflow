FROM apache/airflow:3.4.0-python3.13

# Copy your requirements definition file
COPY --chown=airflow:root requirements.txt /requirements.txt

# Install packages into the container layer
RUN pip install --no-cache-dir -r /requirements.txt

FROM apache/airflow:2.10.3

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jdk procps && \
    ln -s /usr/lib/jvm/java-17-openjdk-amd64 /usr/lib/jvm/java-11-openjdk-amd64 && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

USER airflow

RUN pip install --no-cache-dir pandas pyspark

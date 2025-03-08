"""
ETL Pipeline for CMS Outpatient Data
Author: Sean Lee
Date: 2025-03-08
"""

import requests
from pyspark.sql import SparkSession
from pyspark.sql.functions import monotonically_increasing_id, col, round
from pyspark.sql.types import DoubleType
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Configuration Constants
CMS_DATA_URL = "https://data.cms.gov/data-api/v1/dataset/ccbc9a44-40d4-46b4-a709-5caa59212e50/data"
RAW_DATA_PATH = "/opt/airflow/raw_data/raw_data.parquet"
TRANSFORMED_DATA_PATH = "/opt/airflow/transform_data/transform_data.parquet"

# Extract data from CMS API and store as Parquet file
def extract_function():

    try:
        # Extract data from API
        response = requests.get(CMS_DATA_URL, timeout=30)
        response.raise_for_status()
        json_data = response.json()

        spark = SparkSession.builder.appName("extract_data").getOrCreate()
        df = spark.createDataFrame(json_data)

        # Save raw data
        df.write.mode("overwrite").format("parquet").save(RAW_DATA_PATH)

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Data extraction failed: {str(e)}") from e

    except Exception as e:
        raise RuntimeError(f"Unexpected error in extraction: {str(e)}") from e

    finally:
        if 'spark' in locals():
            spark.stop()


# Transform raw data and load processed results
def transform_and_load_function():

    try:
        spark = SparkSession.builder.appName("transform_and_load_data").getOrCreate()

        raw_df = spark.read.parquet(RAW_DATA_PATH)
        raw_df.createOrReplaceTempView("outpatient")

        transform_df = spark.sql("""
            SELECT
                Rndrng_Prvdr_CCN AS nurse_id,
                Rndrng_Prvdr_Org_Name AS organisation,
                Rndrng_Prvdr_St AS street,
                Rndrng_Prvdr_City AS city,
                APC_Cd AS payment_classification_id,
                APC_Desc AS APC_description,
                Avg_Tot_Sbmtd_Chrgs AS submitted_charges,
                Avg_Mdcr_Alowd_Amt AS medicare_allowed_amount,
                Avg_Mdcr_Pymt_Amt AS medicare_payment_amount
            FROM outpatient
        """)
        
        # Add unique ID column
        transform_df = transform_df.withColumn("id", monotonically_increasing_id())

        # Type casting
        transform_df = transform_df.withColumn("submitted_charges", round(col("submitted_charges"), 2).cast(DoubleType()))
        transform_df = transform_df.withColumn("medicare_allowed_amount", round(col("medicare_allowed_amount"), 2).cast(DoubleType()))
        transform_df = transform_df.withColumn("medicare_payment_amount", round(col("medicare_payment_amount"), 2).cast(DoubleType()))

        # Add new personal payment amount
        transform_df = transform_df.withColumn("personal_payment_amount", round(col("submitted_charges") - col("medicare_payment_amount"), 2).cast(DoubleType()))

        # Reorder columns with ID first
        columns = ["id"] + [col for col in transform_df.columns if col != "id"]
        transform_df = transform_df.select(columns)

        # Save transformed data
        transform_df.write.mode("overwrite").format("parquet").save(TRANSFORMED_DATA_PATH)

    except Exception as e:
        raise RuntimeError(f"Transformation failed: {str(e)}") from e

    finally:
        if 'spark' in locals():
            spark.stop()

# DAG Configuration
default_args = {
    "owner": "airflow",
    "start_date": datetime(2025, 3, 7),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False
}

dag = DAG(
    dag_id="ETL_cms_outpatient",
    default_args=default_args,
    description="CMS Outpatient Data Processing ETL Pipeline",
    schedule="0 12 * * *",
    catchup=False
)

extract_task = PythonOperator(task_id="extract_function", python_callable=extract_function, dag=dag)
transform_and_load_task = PythonOperator(task_id="transform_and_load_function", python_callable=transform_and_load_function, dag=dag)

extract_task >> transform_and_load_task
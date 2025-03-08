**CMS Outpatient Data Processing ETL Pipeline**

This project is an end-to-end ETL (Extract, Transform, Load) pipeline built with Apache Airflow and PySpark. It extracts outpatient data from the CMS API, transforms the data using PySpark, and loads the processed results into Parquet files for further analysis. The project is containerized using Docker Compose and leverages a custom Airflow image with Java 17, Pandas, and PySpark installed.

**Features**
* Data Extraction: Retrieves data from the CMS API and saves it as a raw Parquet file.
* Data Transformation: Uses PySpark to:
  * Filter and select relevant columns
  * Add a unique identifier
  * Round and cast numerical values
  * Compute a new field (personal_payment_amount)
* Scheduling: Automated daily execution using Apache Airflow’s scheduler.
* Containerized Environment: All components (Airflow, Postgres, etc.) are run in Docker containers for a consistent and isolated setup.

**Project Structure**
<pre style="white-space: pre; overflow: auto;">
.
├── dags
│   └── etl_cms_outpatient.py        # Airflow DAG definition
├── logs                             # Airflow logs directory
├── plugins                          # Airflow plugins (if any)
├── raw_data                         # Directory to store raw Parquet files
├── transform_data                   # Directory to store transformed Parquet files
└── docker-compose.yaml              # Docker Compose configuration
</pre>


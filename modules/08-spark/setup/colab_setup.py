"""
Module 08 · Setup · Colab environment bootstrap

Run this ONCE at the top of a fresh Colab notebook before any Spark work.
Sets up:
  1. PySpark installation (Colab pre-installs it, but pin the version)
  2. PostgreSQL JDBC driver download to /content/postgresql.jar
  3. A SparkSession pre-configured with the JDBC driver on the classpath

Locally: the same setup works on Linux/macOS/WSL with Python 3.10+ and Java 11+.
Install PySpark via `pip install pyspark==3.5.*` first.
"""

import os
import subprocess
import urllib.request

# -----------------------------------------------------------------------
# 1. Ensure PySpark is available (Colab already ships it, but pin version)
# -----------------------------------------------------------------------
try:
    import pyspark
    print(f"[setup] PySpark {pyspark.__version__} already installed")
except ImportError:
    print("[setup] Installing PySpark ...")
    subprocess.check_call(["pip", "install", "--quiet", "pyspark==3.5.1"])
    import pyspark
    print(f"[setup] PySpark {pyspark.__version__} installed")


# -----------------------------------------------------------------------
# 2. PostgreSQL JDBC driver — required for reading from NovaBuild DB
# -----------------------------------------------------------------------
JDBC_JAR = "/content/postgresql.jar"
JDBC_URL = ("https://jdbc.postgresql.org/download/postgresql-42.7.3.jar")

if not os.path.exists(JDBC_JAR):
    print(f"[setup] Downloading PostgreSQL JDBC driver -> {JDBC_JAR}")
    urllib.request.urlretrieve(JDBC_URL, JDBC_JAR)
    print("[setup] Driver downloaded")
else:
    print(f"[setup] JDBC driver already at {JDBC_JAR}")


# -----------------------------------------------------------------------
# 3. Build a SparkSession with the driver on the classpath
# -----------------------------------------------------------------------
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("NovaBuildModule08")
    .config("spark.jars", JDBC_JAR)
    # Adaptive Query Execution — Section 8.8 discusses this in depth.
    .config("spark.sql.adaptive.enabled", "true")
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
    # Keep executor memory reasonable on Colab.
    .config("spark.executor.memory", "2g")
    .config("spark.driver.memory", "2g")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")
print(f"[setup] SparkSession ready — Spark {spark.version}")

# -----------------------------------------------------------------------
# 4. JDBC connection properties reused across every section
# -----------------------------------------------------------------------
# Override these via environment variables when running locally.
jdbc_url = os.environ.get(
    "PG_JDBC_URL",
    "jdbc:postgresql://your-host:5432/novabuilds",
)
jdbc_props = {
    "user": os.environ.get("PG_USER", "saas_user"),
    "password": os.environ.get("PG_PASSWORD", "saas_pass"),
    "driver": "org.postgresql.Driver",
}

print("[setup] JDBC connection properties configured")
print("[setup] Ready to run Module 08 sections")

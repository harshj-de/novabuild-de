"""
Module 08 · Section 8.7 — UDFs (User Defined Functions)

Sometimes built-in Spark functions don't cover your business logic.
UDFs let you write plain Python and apply it to a DataFrame column.

But: UDFs are SLOWER than built-in functions because Spark can't
optimise around them. Use them when necessary; use built-ins when
possible.

Three types of UDF:
  1. Regular Python UDF   — one-row-at-a-time, slowest
  2. Pandas UDF (vectorized) — batched, much faster
  3. SQL-registered UDF   — available inside spark.sql() calls
"""

from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DoubleType, IntegerType

contractors = spark.read.jdbc(url=jdbc_url, table="contractors", properties=jdbc_props)


# =====================================================================
# 1. Regular Python UDF
# =====================================================================

# Step 1 — the plain Python function.
def risk_flag(emr):
    """Return a categorical risk flag from a contractor's EMR."""
    if emr is None:
        return "Unknown"
    if emr > 1.5:
        return "Critical"
    elif emr > 1.25:
        return "High"
    elif emr >= 1.0:
        return "Medium"
    else:
        return "Low"


# Step 2 — register it as a Spark UDF, declaring the return type.
risk_flag_udf = F.udf(risk_flag, StringType())


# Step 3 — apply to a column.
contractors_flagged = contractors.withColumn(
    "risk_flag",
    risk_flag_udf(F.col("emr")),
)

contractors_flagged.select("company_name", "tier", "emr", "risk_flag") \
    .orderBy("emr", ascending=False).show(10)


# =====================================================================
# 2. Pandas UDF (vectorised) — much faster
# =====================================================================
# Instead of processing one row at a time, Pandas UDFs process a whole
# batch of rows as a pandas Series. Spark ships Arrow batches to Python
# and back — the overhead is amortised.

from pyspark.sql.functions import pandas_udf
import pandas as pd

@pandas_udf(StringType())
def risk_flag_vec(emr_series: pd.Series) -> pd.Series:
    """Vectorised version — operates on a Series at a time."""
    def label(v):
        if pd.isna(v):        return "Unknown"
        if v > 1.5:           return "Critical"
        elif v > 1.25:        return "High"
        elif v >= 1.0:        return "Medium"
        else:                 return "Low"
    return emr_series.map(label)


contractors_flagged_v = contractors.withColumn(
    "risk_flag",
    risk_flag_vec(F.col("emr")),
)

# On big data, vectorised UDFs are 5-100x faster than regular UDFs.


# =====================================================================
# 3. SQL-registered UDF — for use inside spark.sql()
# =====================================================================
# Register the function so it's callable from SQL.

spark.udf.register("risk_flag_sql", risk_flag, StringType())

contractors.createOrReplaceTempView("contractors")

spark.sql("""
    SELECT
        company_name,
        tier,
        emr,
        risk_flag_sql(emr) AS risk_flag
    FROM contractors
    ORDER BY emr DESC
    LIMIT 10
""").show()


# =====================================================================
# When NOT to use UDFs
# =====================================================================
# The vast majority of business logic can be expressed with when/otherwise:

contractors_native = contractors.withColumn(
    "risk_flag",
    F.when(F.col("emr").isNull(), "Unknown")
     .when(F.col("emr") > 1.5, "Critical")
     .when(F.col("emr") > 1.25, "High")
     .when(F.col("emr") >= 1.0, "Medium")
     .otherwise("Low"),
)

# This is:
#   * Vectorised (native Catalyst code)
#   * Optimisable (Catalyst can push down predicates through it)
#   * Faster than even a Pandas UDF
#   * Type-safe at plan time
#
# Rule of thumb: reach for a UDF only when native functions can't do it.

# =====================================================================
# Concepts demonstrated
#
#   * Regular Python UDF — the simplest, slowest option
#   * Pandas UDF — vectorised, much faster on big data
#   * SQL-registered UDF — callable from spark.sql()
#   * When to reach for a UDF vs when to use native when()/otherwise
# =====================================================================

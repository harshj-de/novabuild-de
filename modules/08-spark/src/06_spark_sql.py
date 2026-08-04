"""
Module 08 · Section 8.6 — Spark SQL

Every DataFrame can be registered as a temporary view, and you can then
run SQL against it just like a database. Under the hood Spark plans and
executes the same way as the DataFrame API — SQL is just a different
front door to the Catalyst optimiser.

This section demonstrates 16 practice queries against the NovaBuild
schema, mixing standard SQL, window functions, and joins.
"""

from pyspark.sql import functions as F

# -----------------------------------------------------------------------
# Setup — register all tables as temp views
# -----------------------------------------------------------------------
tables = ["claims", "contractors", "safety_incidents", "certificates",
          "policies", "carriers", "brokers", "sponsors"]

for t in tables:
    df = spark.read.jdbc(url=jdbc_url, table=t, properties=jdbc_props)
    df.createOrReplaceTempView(t)

print("Registered views:")
for tbl in spark.catalog.listTables():
    print(f"  {tbl.name:<24} isTemporary: {tbl.isTemporary}")


# =====================================================================
# Q1 — Top 10 claims by incurred loss
# =====================================================================
spark.sql("""
    SELECT claim_id, carrier_id, incurred_loss, status
    FROM claims
    ORDER BY incurred_loss DESC
    LIMIT 10
""").show(truncate=False)


# =====================================================================
# Q2 — Distinct claim statuses
# =====================================================================
spark.sql("SELECT DISTINCT status FROM claims").show()


# =====================================================================
# Q3 — Count of Open claims above $500k
# =====================================================================
spark.sql("""
    SELECT COUNT(*) AS big_open_claims
    FROM claims
    WHERE status = 'Open'
      AND incurred_loss > 500000
""").show()


# =====================================================================
# Q4 — Total and average loss by claim type
# =====================================================================
spark.sql("""
    SELECT
        claim_type,
        COUNT(*)                     AS claim_count,
        ROUND(SUM(incurred_loss), 2) AS total_loss,
        ROUND(AVG(incurred_loss), 2) AS avg_loss
    FROM claims
    GROUP BY claim_type
    ORDER BY total_loss DESC
""").show()


# =====================================================================
# Q5 — Contractors by tier — count + average EMR
# =====================================================================
spark.sql("""
    SELECT
        tier,
        COUNT(*)                AS contractor_count,
        ROUND(AVG(emr), 2)      AS avg_emr
    FROM contractors
    GROUP BY tier
    ORDER BY avg_emr DESC
""").show()


# =====================================================================
# Q6 — Certificates expiring in 30 days
# =====================================================================
spark.sql("""
    SELECT
        certificate_id,
        contractor_id,
        expiration_date,
        DATEDIFF(expiration_date, CURRENT_DATE()) AS days_until_expiry
    FROM certificates
    WHERE expiration_date BETWEEN CURRENT_DATE() AND DATE_ADD(CURRENT_DATE(), 30)
    ORDER BY expiration_date
""").show(10)


# =====================================================================
# Q7 — Claims joined with carrier name (INNER JOIN)
# =====================================================================
spark.sql("""
    SELECT
        c.claim_id,
        c.incurred_loss,
        ca.carrier_name
    FROM claims c
    INNER JOIN carriers ca ON c.carrier_id = ca.carrier_id
    ORDER BY c.incurred_loss DESC
    LIMIT 10
""").show(truncate=False)


# =====================================================================
# Q8 — LEFT JOIN + IS NULL — claims without a carrier
# =====================================================================
spark.sql("""
    SELECT c.claim_id, c.carrier_id
    FROM claims c
    LEFT JOIN carriers ca ON c.carrier_id = ca.carrier_id
    WHERE ca.carrier_id IS NULL
""").show()


# =====================================================================
# Q9 — Multi-table join (claims -> contractors -> carriers)
# =====================================================================
spark.sql("""
    SELECT
        c.claim_id,
        ct.company_name,
        ct.tier,
        ca.carrier_name,
        c.incurred_loss
    FROM claims c
    JOIN contractors ct ON c.contractor_id = ct.contractor_id
    JOIN carriers    ca ON c.carrier_id    = ca.carrier_id
    WHERE ct.tier = 'Preferred'
    ORDER BY c.incurred_loss DESC
    LIMIT 10
""").show(truncate=False)


# =====================================================================
# Q10 — Claims above the average incurred loss (subquery)
# =====================================================================
spark.sql("""
    SELECT claim_id, incurred_loss
    FROM claims
    WHERE incurred_loss > (SELECT AVG(incurred_loss) FROM claims)
    ORDER BY incurred_loss DESC
    LIMIT 10
""").show()


# =====================================================================
# Q11 — Contractors above average incident count (correlated subquery)
# =====================================================================
spark.sql("""
    WITH incident_counts AS (
        SELECT contractor_id, COUNT(*) AS n_incidents
        FROM safety_incidents
        GROUP BY contractor_id
    ),
    avg_incidents AS (
        SELECT AVG(n_incidents) AS avg_n FROM incident_counts
    )
    SELECT ct.company_name, ic.n_incidents
    FROM contractors ct
    JOIN incident_counts ic ON ct.contractor_id = ic.contractor_id
    CROSS JOIN avg_incidents
    WHERE ic.n_incidents > avg_incidents.avg_n
    ORDER BY ic.n_incidents DESC
""").show(10)


# =====================================================================
# Q12 — CTE for readability (same as Q11 restated)
# =====================================================================
# CTEs are the readable way to layer multiple aggregations.
# Prefer WITH clauses over deeply nested subqueries. Every CTE
# is essentially a temporary named view for the query.


# =====================================================================
# Q13 — ROW_NUMBER — top-N per group (contractors by tier)
# =====================================================================
spark.sql("""
    SELECT company_name, tier, emr, rn
    FROM (
        SELECT
            company_name,
            tier,
            emr,
            ROW_NUMBER() OVER (PARTITION BY tier ORDER BY emr DESC) AS rn
        FROM contractors
    )
    WHERE rn <= 3
    ORDER BY tier, rn
""").show()


# =====================================================================
# Q14 — ROW_NUMBER vs RANK vs DENSE_RANK side by side
# =====================================================================
spark.sql("""
    SELECT
        contractor_id,
        emr,
        ROW_NUMBER() OVER (ORDER BY emr DESC) AS rn,
        RANK()       OVER (ORDER BY emr DESC) AS rk,
        DENSE_RANK() OVER (ORDER BY emr DESC) AS drk
    FROM contractors
    LIMIT 15
""").show()


# =====================================================================
# Q15 — NTILE(4) — quartile bucketing of contractors by EMR
# =====================================================================
spark.sql("""
    SELECT
        contractor_id,
        emr,
        NTILE(4) OVER (ORDER BY emr) AS emr_quartile
    FROM contractors
    ORDER BY emr
""").show(20)


# =====================================================================
# Q16 — NTILE with business label
# =====================================================================
spark.sql("""
    SELECT
        contractor_id,
        emr,
        CASE NTILE(4) OVER (ORDER BY emr)
            WHEN 1 THEN 'Best (lowest EMR)'
            WHEN 2 THEN 'Good'
            WHEN 3 THEN 'Watch'
            WHEN 4 THEN 'High Risk'
        END AS risk_bucket
    FROM contractors
    ORDER BY emr
""").show(20)


# -----------------------------------------------------------------------
# Storing SQL results as DataFrames
# -----------------------------------------------------------------------
# spark.sql() returns a DataFrame — chain any DataFrame method after.

loss_ratio = spark.sql("""
    SELECT
        c.carrier_id,
        ca.carrier_name,
        ROUND(SUM(c.incurred_loss) / NULLIF(SUM(p.premium_amount), 0), 4)
            AS loss_ratio
    FROM claims c
    JOIN carriers ca ON c.carrier_id = ca.carrier_id
    JOIN policies p  ON c.policy_id  = p.policy_id
    GROUP BY c.carrier_id, ca.carrier_name
    ORDER BY loss_ratio DESC
""")

loss_ratio.show(10)

# You can now .write it, .filter it further, .join it — it's a DataFrame.


# =====================================================================
# When to use SQL vs DataFrame API
#
#   SQL is best for:
#     * Analysts on the team — universal skill
#     * Ad-hoc exploration in Spark SQL / Databricks SQL
#     * Complex joins/aggregations where SQL reads better
#
#   DataFrame API is best for:
#     * Programmatic code (loops, function composition)
#     * Testing (easier to mock DataFrames)
#     * Cases where SQL string manipulation would get ugly
#
#   Both plan to the same execution — Catalyst doesn't care.
# =====================================================================

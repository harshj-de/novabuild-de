# NovaBuild Schema Reference for Module 08

The PySpark files in `src/` join against these tables. If you already
have the NovaBuild dataset loaded (from Module 06 or Module 12), you're
ready to go. Otherwise, follow the getting-started section in the
Module 12 (FastAPI) README to load seed data.

---

## Tables referenced

| Table | Rows (approx) | Notes |
|---|---|---|
| `contractors` | ~7,500 | Contractor master data (tier, EMR, employees) |
| `claims` | ~15,000 | Claim events (loss_date, incurred_loss, status) |
| `safety_incidents` | ~24,000 | Recorded safety incidents (severity, osha_recordable) |
| `certificates` | ~9,000 | COI certificates (expiration_date) |
| `policies` | ~8,000 | Insurance policies (broker_id, carrier_id, premium_amount) |
| `carriers` | ~40 | Insurance carriers |
| `brokers` | ~180 | Brokers |
| `sponsors` | ~30 | Wrap-up program sponsors |

---

## Connection strings

The setup script reads from environment variables. Set them before
running any file:

```bash
export PG_JDBC_URL="jdbc:postgresql://your-host:5432/novabuilds"
export PG_USER="saas_user"
export PG_PASSWORD="saas_pass"
```

On Colab, use `os.environ["PG_JDBC_URL"] = "..."` in a cell before
`%run setup/colab_setup.py`.

---

## Local Postgres alternative

If running against a local Postgres:

```bash
docker run -d --name novabuilds \
    -e POSTGRES_USER=saas_user \
    -e POSTGRES_PASSWORD=saas_pass \
    -e POSTGRES_DB=novabuilds \
    -p 5432:5432 \
    postgres:16

# Load the schema + seed from Module 12
psql -h localhost -U saas_user -d novabuilds -f /path/to/module12/setup/schema.sql
python /path/to/module12/setup/seed_novabuilds.py
```

Then point Spark at `jdbc:postgresql://localhost:5432/novabuilds`.

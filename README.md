# Bechtel Invoice Data — ClickHouse Ingestion

Loads `bechtel_invoices_fully_enriched.csv` (405 columns, ~9,800 rows) into
`invoice_extraction.con_master_fact`.

---

## Step 1 — Start ClickHouse

```bash
docker run -d --name clickhouse \
  -p 9001:9000 \
  -p 8124:8123 \
  -e CLICKHOUSE_USER=admin \
  -e CLICKHOUSE_PASSWORD=admin123 \
  -e CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1 \
  clickhouse/clickhouse-server:latest
```

---

## Step 2 — Create Database and Table

```bash
clickhouse client \
  --host localhost \
  --port 9001 \
  --user admin \
  --password admin123 \
  --query="CREATE DATABASE IF NOT EXISTS invoice_extraction"
```

```bash
clickhouse client \
  --host localhost \
  --port 9001 \
  --user admin \
  --password admin123 \
  --database invoice_extraction \
  --queries-file construction_schema/con_master_fact.sql
```

---

## Step 3 — Insert the CSV

```bash
clickhouse client \
  --host localhost \
  --port 9001 \
  --user admin \
  --password admin123 \
  --database invoice_extraction \
  --query="INSERT INTO con_master_fact FORMAT CSVWithNames" \
  < bechtel_invoices_fully_enriched.csv
```

> `CSVWithNames` reads the header row from the file and maps columns by name automatically.

---

## Verify

```bash
clickhouse client \
  --host localhost \
  --port 9001 \
  --user admin \
  --password admin123 \
  --database invoice_extraction \
  --query="SELECT count() FROM con_master_fact FINAL"
```

Expected output: `9804`

---

## Sample Queries

```sql
-- Spend by vendor
SELECT vnd_vendor_name_normalized,
       round(sum(inv_total_amount) / 1e6, 2) AS spend_usd_m
FROM invoice_extraction.con_master_fact FINAL
GROUP BY vnd_vendor_name_normalized
ORDER BY spend_usd_m DESC
LIMIT 10;

-- Spend by EPC category
SELECT inv_li_epc_category,
       count()                                AS line_items,
       round(sum(inv_total_amount) / 1e6, 2)  AS spend_usd_m
FROM invoice_extraction.con_master_fact FINAL
GROUP BY inv_li_epc_category
ORDER BY spend_usd_m DESC;

-- Overdue invoices
SELECT invoice_id, inv_invoice_date, pmt_overdue_days, inv_total_amount
FROM invoice_extraction.con_master_fact FINAL
WHERE pmt_overdue_flag = 1
ORDER BY pmt_overdue_days DESC;
```

> Always use `FINAL` — the table uses `ReplacingMergeTree` which deduplicates by
> `(transaction_id, line_item_id)` at query time when `FINAL` is specified.

---

## Python Insert (alternative)

If the `clickhouse client` binary is not available, use the Python script:

```bash
pip install clickhouse-driver
python insert_to_clickhouse.py --csv bechtel_invoices_fully_enriched.csv
```

Connection defaults are in `constants.py`. Override at runtime:

```bash
python insert_to_clickhouse.py \
  --csv bechtel_invoices_fully_enriched.csv \
  --host localhost --port 9001 \
  --user admin --password admin123 \
  --database invoice_extraction
```

---

## Files

| File | Purpose |
|---|---|
| `bechtel_invoices_fully_enriched.csv` | Source data — 405 columns, ~9,800 rows |
| `construction_schema/con_master_fact.sql` | Table DDL + materialized views |
| `insert_to_clickhouse.py` | Python insert script (alternative) |
| `constants.py` | ClickHouse connection defaults |

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `Connection refused` | ClickHouse not running or wrong port | Check Docker is up; use `--port 9001` for Docker host mapping |
| `authentication failed` | Wrong credentials | Match `--user` / `--password` to your Docker `-e` flags |
| `Table doesn't exist` | Schema not created yet | Run Step 2 first |
| `Too many partitions` (Python only) | Wide date range per batch | Already handled in Python script — script sorts by date |

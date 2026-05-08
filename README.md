# Bechtel → ClickHouse Data Ingestion

Inserts Bechtel invoice CSV data into the `con_master_fact` ClickHouse table (405 columns).

## Prerequisites

**Python packages**
```bash
pip install clickhouse-driver pandas
```

**ClickHouse via Docker**

The project expects ClickHouse running with these port mappings:
- `9001` → native TCP (used by `clickhouse-driver`)
- `8124` → HTTP interface

```bash
docker run -d \
  --name gangster-clickhouse \
  -p 9001:9000 \
  -p 8124:8123 \
  -e CLICKHOUSE_USER=admin \
  -e CLICKHOUSE_PASSWORD=admin123 \
  -e CLICKHOUSE_DB=invoice_extraction \
  clickhouse/clickhouse-server:24.3
```

Verify it's healthy:
```bash
docker ps | grep clickhouse
```

## Running the Script

**Default run (uses `bechtel_invoices_v2.csv`)**
```bash
python insert_to_clickhouse.py --csv bechtel_invoices_v2.csv
```

**Dry run — parses and prints 2 rows, no insert**
```bash
python insert_to_clickhouse.py --csv bechtel_invoices_v2.csv --dry-run
```

**Custom connection**
```bash
python insert_to_clickhouse.py \
  --csv bechtel_invoices_v2.csv \
  --host localhost \
  --port 9001 \
  --user admin \
  --password admin123 \
  --database invoice_extraction
```

### All Options

| Flag | Default | Description |
|------|---------|-------------|
| `--csv` | `bechtel_invoices_v2.csv` | Path to the invoices CSV |
| `--host` | `localhost` | ClickHouse host |
| `--port` | `9001` | ClickHouse **native TCP** port (not the HTTP port) |
| `--user` | `admin` | ClickHouse user |
| `--password` | `admin123` | ClickHouse password |
| `--database` | `invoice_extraction` | Target database |
| `--table` | `con_master_fact` | Target table |
| `--batch` | `500` | Rows per insert batch |
| `--dry-run` | off | Preview rows without inserting |

## What the Script Does

1. Reads the CSV (63 extracted columns)
2. Casts and expands every row to all 405 columns (remaining columns default to NULL/0)
3. Sorts rows by `inv_invoice_date` to minimise partition spread per batch
4. Inserts in batches of 500 rows into `con_master_fact`
5. Creates the table automatically if it doesn't exist (reads `construction_schema/con_master_fact.sql`)
6. Runs verification queries after insert

## Common Errors

**`Unexpected packet from server` on connect**
You're hitting the HTTP port (8124) instead of the native TCP port. Use `--port 9001`.

**`Too many partitions for single INSERT block`**
The data spans too many invoice-date months in one batch. This is already handled by sorting rows before insert and passing `max_partitions_per_insert_block=1000` per query. If it still occurs, reduce `--batch` to 100.

**`Table con_master_fact not found`**
The script will auto-create it from `construction_schema/con_master_fact.sql`. Make sure that file exists before running.

"""
Count NULL / empty-string values per column in con_master_fact.
Single-pass query — does not hit the table once per column.

Usage:
  python check_empty_columns.py
  python check_empty_columns.py --min-pct 50        # only columns ≥ 50% empty
  python check_empty_columns.py --show-full          # include 100%-empty columns
"""

import argparse
from clickhouse_driver import Client
from constants import (
    CLICKHOUSE_HOST as HOST,
    CLICKHOUSE_PORT as PORT,
    CLICKHOUSE_USER as USER,
    CLICKHOUSE_PASSWORD as PASSWORD,
    CLICKHOUSE_DATABASE as DATABASE,
    CLICKHOUSE_TABLE as TABLE,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-pct",   type=float, default=0,
                        help="Only show columns with empty% >= this value")
    parser.add_argument("--show-full", action="store_true",
                        help="Include columns that are 100% empty")
    args = parser.parse_args()

    client = Client(host=HOST, port=PORT, user=USER,
                    password=PASSWORD, database=DATABASE)

    # Get column names + types from ClickHouse metadata
    cols = client.execute(
        f"SELECT name, type FROM system.columns "
        f"WHERE database = '{DATABASE}' AND table = '{TABLE}' "
        f"ORDER BY position"
    )
    if not cols:
        print(f"No columns found for {DATABASE}.{TABLE}")
        return

    col_names = [c[0] for c in cols]
    col_types = {c[0]: c[1] for c in cols}

    # Build a single-pass query:
    #   COUNT empty per column → stored in arrays → ARRAY JOIN to unpivot
    def empty_expr(col, typ):
        if "String" in typ:
            return f"countIf({col} IS NULL OR {col} = '')"
        return f"countIf({col} IS NULL)"

    names_arr  = "[" + ", ".join(f"'{c}'" for c in col_names) + "]"
    counts_arr = "[" + ", ".join(empty_expr(c, col_types[c]) for c in col_names) + "]"

    query = f"""
        SELECT
            col,
            empty_count,
            total_rows,
            round(empty_count * 100.0 / total_rows, 1) AS empty_pct
        FROM (
            SELECT
                count()       AS total_rows,
                {names_arr}   AS col_names,
                {counts_arr}  AS empty_counts
            FROM {DATABASE}.{TABLE} FINAL
        )
        ARRAY JOIN col_names AS col, empty_counts AS empty_count
        ORDER BY empty_count DESC
    """

    rows = client.execute(query)
    if not rows:
        print("Table is empty.")
        return

    total_rows = rows[0][2]

    # Apply filters
    if not args.show_full:
        rows = [r for r in rows if r[1] < total_rows]
    if args.min_pct > 0:
        rows = [r for r in rows if r[3] >= args.min_pct]

    # Print
    print(f"\n  Table : {DATABASE}.{TABLE}")
    print(f"  Rows  : {total_rows:,}")
    print(f"  Cols  : {len(col_names)}\n")
    print(f"  {'Column':<45} {'Empty':>10} {'Empty %':>9}")
    print("  " + "-" * 67)

    for col, empty_count, _, pct in rows:
        bar = "█" * int(pct / 5)
        print(f"  {col:<45} {empty_count:>10,} {pct:>8.1f}%  {bar}")

    fully_empty   = sum(1 for _, e, t, _ in client.execute(query) if e == t)
    has_some_data = sum(1 for _, e, t, _ in client.execute(query) if 0 < e < t)
    fully_filled  = sum(1 for _, e, _, _ in client.execute(query) if e == 0)

    print(f"\n  Summary")
    print(f"  {'Fully filled (0% empty)':<35} {fully_filled}")
    print(f"  {'Partially empty':<35} {has_some_data}")
    print(f"  {'Fully empty (100%)':<35} {fully_empty}")


if __name__ == "__main__":
    main()

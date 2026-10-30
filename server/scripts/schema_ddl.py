"""Generate CREATE TABLE statements for a local test MySQL from docs/rohdaten/columns.json.

Only structure (columns, types, NULL, defaults, PK/UNIQUE/INDEX) – no data. Used by the integration tests.
Usage: python3 -I scripts/schema_ddl.py [table ...] > schema.sql
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROH = os.path.abspath(os.path.join(HERE, "..", "..", "docs", "rohdaten"))


def load():
    cols = json.load(open(os.path.join(ROH, "columns.json"), encoding="utf-8"))["rows"]
    defaults = {(r[0], r[1]): (r[2], r[3]) for r in json.load(open(os.path.join(ROH, "column_defaults.json"), encoding="utf-8"))["rows"]}
    tables = {}
    for r in cols:
        tables.setdefault(r["t"], []).append(r)
    for t in tables.values():
        t.sort(key=lambda r: int(r["pos"]))
    return tables, defaults


def ddl(table, rows, defaults, auto_increment_int_pk=False):
    """auto_increment_int_pk: test convenience – single int PKs get AUTO_INCREMENT (not in snapshot for all tables)."""
    n_pk = sum(1 for r in rows if r["ckey"] == "PRI")
    lines, pk, keys = [], [], []
    for r in rows:
        col, typ = r["col"], r["typ"]
        d, extra = defaults.get((table, col), (None, ""))
        s = f"  `{col}` {typ} " + ("NULL" if r["nullable"] == "YES" else "NOT NULL")
        if extra == "auto_increment" or (auto_increment_int_pk and r["ckey"] == "PRI" and n_pk == 1 and typ.startswith("int")):
            s += " AUTO_INCREMENT"
        elif d is not None:
            s += " DEFAULT CURRENT_TIMESTAMP" if d == "CURRENT_TIMESTAMP" else " DEFAULT " + ("'" + d.replace("'", "''") + "'")
        lines.append(s)
        if r["ckey"] == "PRI":
            pk.append(col)
        elif r["ckey"] == "UNI":
            keys.append(f"  UNIQUE KEY `u_{col}` (`{col}`)")
        elif r["ckey"] == "MUL":
            keys.append(f"  KEY `i_{col}` (`{col}`)")
    if pk:
        lines.append("  PRIMARY KEY (" + ", ".join(f"`{c}`" for c in pk) + ")")
    lines += keys
    return f"CREATE TABLE `{table}` (\n" + ",\n".join(lines) + "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"


def main(argv):
    tables, defaults = load()
    want = argv or sorted(tables)
    for t in want:
        print(ddl(t, tables[t], defaults))
        print()


if __name__ == "__main__":
    main(sys.argv[1:])

import sqlite3
import json
import os

conn = sqlite3.connect('sales_ops.db')
c = conn.cursor()

def sql_quote(v):
    if v is None:
        return 'NULL'
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v).replace("'", "''")
    return f"'{s}'"

def dump_table(table, batch_size=25):
    c.execute(f"SELECT * FROM {table}")
    col_names = [d[0] for d in c.description if d[0] != 'id']
    rows = c.fetchall()
    batches = []
    current = []
    for r in rows:
        vals = [sql_quote(v) for k, v in zip([d[0] for d in c.description], r) if k != 'id']
        current.append(f"({', '.join(vals)})")
        if len(current) >= batch_size:
            batches.append(f"INSERT INTO {table} ({', '.join(col_names)}) VALUES " + ',\n'.join(current) + ";")
            current = []
    if current:
        batches.append(f"INSERT INTO {table} ({', '.join(col_names)}) VALUES " + ',\n'.join(current) + ";")
    return batches

output = {}
for tbl, bsize in [('projects_sep', 30), ('division_monthly', 30), ('data_quality_issues', 10), ('sales_july', 25)]:
    output[tbl] = dump_table(tbl, bsize)

os.makedirs('scripts', exist_ok=True)
with open('scripts/all_inserts.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2)

print('Generated batches:', {k: len(v) for k, v in output.items()})

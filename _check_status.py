import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect('clinica.db')
cur = conn.cursor()

print("=== Linhas com 'Refer' no status ou valor ===")
rows = cur.execute("""
    SELECT id_consulta, id_exame, valor, status
    FROM Resultados_Exames
    WHERE status LIKE '%Refer%' OR valor LIKE '%Refer%'
""").fetchall()
print("Total:", len(rows))
for r in rows:
    print("  ", r)

print()
print("=== Status distintos armazenados ===")
for (s,) in cur.execute("SELECT DISTINCT status FROM Resultados_Exames").fetchall():
    print("  -", s)

conn.close()

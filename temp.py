import sqlite3

table_name = "user_1_sql"
stmt1 = f"SELECT * FROM {table_name}"
stmt2 = f"PRAGMA table_info({table_name})"

with sqlite3.connect("testDB.db", check_same_thread=False) as conn:
    cur = conn.cursor()
    cur.execute(stmt1)  
    rows = cur.fetchall()
    cur.execute(stmt2)
    columnInfos = cur.fetchall()
    columnNames = [item[1] for item in columnInfos]
    columnsType = [item[2] for item in columnInfos]

for row in rows:
    print(list(zip(columnNames, columnsType, row)))

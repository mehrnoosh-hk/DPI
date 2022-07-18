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


# ****************
# ****************
TABLE_NAME = tableName.replace(" ", "")
TABLE_SPEC = []
type_dict = {'string': String, 'number': Integer, 'file': String}
for d in info:
    n = (d['fieldName']).replace(" ", "_").strip()
    t = d['fieldType']
    if t == 'file':
        n = 'fileType_' + n
    TABLE_SPEC.append((n, type_dict[t]))
columns = [Column(n, t) for n, t in TABLE_SPEC]
columns.append(Column('id', Integer, primary_key=True))
columns.append(Column('recordID', Integer))
table = Table(TABLE_NAME, MetaData(), *columns)
table_creation_sql = CreateTable(table)
db.execute(table_creation_sql)
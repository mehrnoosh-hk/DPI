import sqlite3


def create_db_name(id: int, name: str) -> str:
    return "USER_" + str(id) + name.replace(" ", "")

def create_course_Info(rows: list, columnInfos: list):
    columnNames = [(item[1]).replace("_", " ") for item in columnInfos]
    columnsType = [item[2] for item in columnInfos]
    if len(rows) == 0:
        result_dict = []
        field_dict = []
        for i in range(len(columnNames)):
            if columnNames[i] == 'id' or columnNames[i] == 'recordID':
                continue
            mid = {'fieldName': columnNames[i], 'fieldType': columnsType[i]}
            if mid['fieldType'] == 'VARCHAR':
                mid['fieldType'] = 'text'
            if mid['fieldType'] == 'INTEGER':
                mid['fieldType'] = 'number'
            if 'fileType' in mid['fieldName']:
                print("Fuck")
                mid['fieldType'] = 'file'
                mid['fieldName'] = (mid['fieldName']).replace('fileType ', '')
            field_dict.append(mid)
    else:
        result_dict = []
        field_dict = []
        rows = [*rows]
        for row in rows:
            temp = []
            for i in range(len(row)):
                if columnNames[i] == 'id' or columnNames[i] == 'recordID':
                    continue
                mid = {'fieldName': columnNames[i], 'fieldType': columnsType[i], 'fieldValue': row[i]}
                if mid['fieldType'] == 'VARCHAR':
                    mid['fieldType'] = 'text'
                if mid['fieldType'] == 'INTEGER':
                    mid['fieldType'] = 'number'
                if 'فایل' in mid['fieldName'] or 'file' in mid['fieldName']:
                    mid['fieldType'] = 'file'
                    mid['fieldName'] = (mid['fieldName']).replace('fileType ', '')
                temp.append(mid)
            result_dict.append(temp)

        for i in range(len(columnNames)):
            if columnNames[i] == 'id' or columnNames[i] == 'recordID':
                continue
            mid = {'fieldName': columnNames[i], 'fieldType': columnsType[i]}
            if mid['fieldType'] == 'VARCHAR':
                mid['fieldType'] = 'text'
            if mid['fieldType'] == 'INTEGER':
                mid['fieldType'] = 'number'
            if 'fileType' in mid['fieldName']:
                print("Fuck")
                mid['fieldType'] = 'file'
                mid['fieldName'] = (mid['fieldName']).replace('fileType ', '')
            field_dict.append(mid)
    return result_dict, field_dict

def create_update_info(courseInfo: list[dict]):
    col_name = []
    col_value = []
    for d in courseInfo:
        col_name.append(str(d['fieldName']).replace(" ", "_"))
        col_value.append(str(d['fieldValue']))
    col_name_literal = ",".join(col_name)
    col_value_literal = ",".join(f"'{w}'" for w in col_value)
    return col_name_literal, col_value_literal

def reindex(table_name, r: int) -> None:
    sql = """
    UPDATE {table} 
    SET recordID = recordID -1 
    WHERE recordID > {r}
    """.format(table=table_name, r=r)
    with sqlite3.connect("testDB.db", check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.executescript(sql)

import sqlite3
from sqlalchemy import INTEGER, VARCHAR, Column, String, Integer, Table, MetaData
from sqlalchemy.schema import CreateTable
from sqlalchemy.orm import Session


def create_table_name(u_id: str, name: str) -> str:
    return "USER_" + str(u_id) + name.replace(" ", "")

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

def create_put_row_info(courseInfo: list):
    col_name = []
    col_value = []
    for d in courseInfo:
        col_name.append(str(d['fieldName']).replace(" ", "_"))
        col_value.append(d['fieldValue'])
    return [{}]

def reindex(table_name, r: int) -> None:
    sql = """
    UPDATE {table} 
    SET recordID = recordID -1 
    WHERE recordID > {r}
    """.format(table=table_name, r=r)
    with sqlite3.connect("testDB.db", check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.executescript(sql)


def create_table_dynamically(tableName: str, info: list[dict], db: Session):
    # Create a uniqe table name

    TABLE_NAME = tableName.replace(" ", "")
    TABLE_SPEC = []
    type_dict = {'string': String, 'number': Integer, 'file': String}
    for d in info:

        n = (d['fieldName']).replace(" ", "_")
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

def clean_up_course_fields(courseField: list) -> list:
    cleanCourseField = []
    for d in courseField:
        if d["fieldName"] == 'id' or d["fieldName"] == "recordID":
            continue
        d["fieldName"] = d["fieldName"].replace("_", " ")
        if d['fieldType'] == "VARCHAR":
            d['fieldType'] = 'text'
        elif d["fieldType"] == "INTEGER":
            d["fieldType"] = 'number'
        elif 'fileType' in d['fieldName']:
                d['fieldType'] = 'file'
                d['fieldName'] = (d['fieldName']).replace('fileType ', '')
        cleanCourseField.append(d)
    return cleanCourseField

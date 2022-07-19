import sqlite3
from sqlalchemy import INTEGER, VARCHAR, Column, String, Integer, Table, MetaData
from sqlalchemy.schema import CreateTable
from sqlalchemy.orm import Session
from dataAdapter.database import MyFile


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
    type_dict = {'text': String, 'number': Integer, 'file': MyFile}
    for d in info:
        n = (d['fieldName']).strip()
        t = d['fieldType'].strip()
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
    type_dict = {"String": 'text', "INTEGER": 'number',
                 "MyFile": 'file', "VARCHAR": 'text', "file": "file"}
    for d in courseField:
        if d["fieldName"] == 'id' or d["fieldName"] == "recordID":
            continue
        if "fileType_" in d["fieldName"]:
            d["fieldName"] = d["fieldName"].replace("fileType_", "")
            d["fieldType"] = "file"             
        d["fieldType"] = type_dict[d["fieldType"]]
        cleanCourseField.append(d)
    return cleanCourseField

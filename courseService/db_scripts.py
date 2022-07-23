from sqlalchemy import INTEGER, VARCHAR, Column, String, Integer, Table, MetaData, update
from sqlalchemy.schema import CreateTable
from sqlalchemy.orm import Session
from dataAdapter.database import MyFile, engine


def create_put_row_info(courseInfo: list):
    col_name = []
    col_value = []
    for d in courseInfo:
        col_name.append(str(d['fieldName']).replace(" ", "_"))
        col_value.append(d['fieldValue'])
    return [{}]


def reindex(table_name, r: int, db: Session) -> None:
    table_meta = Table(table_name, MetaData(), autoload_with=engine)
    stmt = (
        update(table_meta).
        where(table_meta.c.recordID > r).
        values(recordID = table_meta.c.recordID -1)
    )
    db.execute(stmt)
    db.commit()


def create_table_dynamically(tableName: str, info: list[dict], db: Session):
    # Create a uniqe table name
    TABLE_NAME = tableName
    TABLE_SPEC = []
    type_dict = {'text': String, 'number': Integer, 'file': MyFile, 'string': String}
    for d in info:
        n = (d['fieldName']).strip()
        if n == "ترتیب نمایش":
            continue
        t = d['fieldType'].strip()
        if t == 'file':
            n = 'fileType_' + n
        TABLE_SPEC.append((n, type_dict[t]))
    columns = [Column(n, t) for n, t in TABLE_SPEC]
    columns.append(Column('id', Integer, primary_key=True))
    columns.append(Column('recordID', Integer))
    columns.append(Column('Priority', Integer))  
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
        if d["fieldName"] == "Priority":
            d["fieldName"] = "ترتیب نمایش"           
        d["fieldType"] = type_dict[d["fieldType"]]
        cleanCourseField.append(d)
    return cleanCourseField

def clean_up_course_Info(courseInfo: list) -> list:
    cleanCourseInfo = []
    type_dict = {"String": 'text', "INTEGER": 'number',
                 "MyFile": 'file', "VARCHAR": 'text', "file": "file"}
    for row in courseInfo:
        cleanRow = []
        for d in row:
            if d["fieldName"] == 'id' or d["fieldName"] == "recordID":
                continue
            if "fileType_" in d["fieldName"]:
                d["fieldName"] = d["fieldName"].replace("fileType_", "")
                d["fieldType"] = "file"  
            if d["fieldName"] == "Priority":
                d["fieldName"] = "ترتیب نمایش"           
            d["fieldType"] = type_dict[d["fieldType"]]
            cleanRow.append(d)    
        cleanCourseInfo.append(cleanRow)
    return cleanCourseInfo
import os

import pyodbc


SERVER = os.getenv("EXAMFLOW_DB_SERVER", r".\SQLEXPRESS")
DATABASE = "ExamFlow"
DRIVER = "ODBC Driver 18 for SQL Server"


connection_string = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)


def conectar():
    return pyodbc.connect(connection_string)

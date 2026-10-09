import mysql.connector


def get_connection():
    connection = mysql.connector.connect(
        host="mysql",
        user="root",
        password="root",
        database="ai_hr_attrition_analytics"
    )

    return connection
from typing import Dict, Any
from langchain_core.tools import tool
import sqlite3
import json, os

# 固定的 SQLite 数据库路径

current_file_dir = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(current_file_dir, "example.db")  # 替换为你的数据库文件路径

@tool(
    "execute_sqlite_query",
    description="Execute a SQLite query on a fixed database and return the results as JSON. Use this tool to interact with the SQLite database."
)
def execute_sqlite_query(query: str) -> Dict[str, Any]:
    """
    参数:
        query: 要执行的 SQL 查询
    返回:
        查询结果的 JSON 格式，或者错误信息
    """
    try:
        # 连接到 SQLite 数据库
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 执行查询
        print("---- Executing SQL Query ----")
        print(query)
        cursor.execute(query)
        if query.strip().lower().startswith("select"):
            # 如果是 SELECT 查询，获取所有结果
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            result = {"columns": columns, "rows": rows}
        else:
            # 如果是非 SELECT 查询，提交更改
            conn.commit()
            result = {"message": "Query executed successfully."}

        # 关闭连接
        cursor.close()
        conn.close()

        return {"status": "success", "result": result}

    except sqlite3.Error as e:
        # 捕获 SQLite 错误并返回
        return {"status": "error", "error": str(e)+"--"+query+"--"+DATABASE_PATH}
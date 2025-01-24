import sqlite3
import pandas as pd

class SQLiteModule:
    """
    本类提供了一组方法来简化与SQLite数据库的交互。
    它封装了数据库连接和游标操作，提供了创建表、插入数据、
    查询数据、更新数据和删除数据的功能。
    """
    def __init__(self, db_name):
        """
        构造方法，初始化数据库连接和游标。

        参数:
        - db_name: 数据库的名称，用于建立连接。
        """
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()

    def create_table(self, table_name, columns):
        """
        创建一个新的数据库表。

        参数:
        - table_name: 要创建的表的名称。
        - columns: 一个包含表列定义的列表，每个元素是一个元组 (column_name, column_type)。
        """
        columns_with_types = ', '.join([f"{col} {ctype}" for col, ctype in columns])
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_with_types})")
        self.connection.commit()

    def insert_data(self, table_name, columns, data):
        """
        向指定的表中插入一条数据。

        参数:
        - table_name: 要插入数据的表的名称。
        - columns: 一个包含列名的元组或列表。
        - data: 一个包含要插入的数据的元组或列表，与columns一一对应。
        """
        col_names = ', '.join(columns)
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
        self.cursor.execute(query, data)
        self.connection.commit()

    def update_data(self, table_name, set_columns_values, condition_column, condition_value):
        """
        更新指定表中的数据。

        参数:
        - table_name: 要更新数据的表的名称。
        - set_columns_values: 一个字典，键是要设置的列名，值是要设置的值。
        - condition_column: 更新条件的列名。
        - condition_value: 更新条件的值。
        """
        # 构建 SET 子句
        set_clause = ', '.join([f"{column} = ?" for column in set_columns_values.keys()])

        # 构建完整的 SQL 语句
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {condition_column} = ?"

        # 组合所有参数
        parameters = list(set_columns_values.values()) + [condition_value]

        self.cursor.execute(sql, parameters)
        self.connection.commit()

    def insert_bulk_data(self, table_name, df):
        """
        向指定的表中批量插入数据。

        参数:
        - table_name: 要插入数据的表的名称。
        - df: 一个pandas DataFrame，包含要插入的数据。
        """
        df.to_sql(table_name, self.connection, if_exists='append', index=False)

    # pd读取数据库数据
    def fetch_data_to_df(self, table_name, condition=None):
        """
        从指定的表中获取所有数据并将其读入DataFrame。

        参数:
        table_name (str): 表名，用于构造SQL查询语句。

        返回:
        DataFrame: 包含指定表中所有数据的DataFrame。
        """
        # 使用pd.read_sql_query方法执行SQL查询并将结果读入DataFrame
        if condition:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE {condition}", self.connection)
        else:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", self.connection)
        return df

    def query_cond(self, table_name, condition=None):
        """
        查询 users 表中的数据，支持条件查询。
        :param table_name: 表名
        :param condition: SQL WHERE 子句中的条件字符串，例如 "age > 25"
        :return: 查询结果列表
        """
        # 构建 SQL 查询语句
        base_query = f"SELECT * FROM {table_name}"
        if condition:
            full_query = f"{base_query} WHERE {condition}"
        else:
            full_query = base_query
        # 执行查询
        self.cursor.execute(full_query)
        rows = self.cursor.fetchall()
        return rows

    def fetch_data(self, table_name):
        """
        从指定的表中获取所有数据。

        参数:
        - table_name: 要查询的表的名称。

        返回:
        - 一个包含查询结果的列表。
        """
        self.cursor.execute(f"SELECT * FROM {table_name}")
        return self.cursor.fetchall()


    def delete_data(self, table_name, condition_column, condition_value):
        """
        从指定表中删除数据。

        参数:
        - table_name: 要删除数据的表的名称。
        - condition_column: 删除条件的列名。
        - condition_value: 删除条件的值。
        """
        self.cursor.execute(f"DELETE FROM {table_name} WHERE {condition_column} = ?", (condition_value,))
        self.connection.commit()

    def close(self):
        """
        关闭数据库连接。
        """
        self.connection.close()

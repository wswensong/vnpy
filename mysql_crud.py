import pymysql.cursors

class MySQLInterface:
    def __init__(self, host, database, user, password):
        """
        初始化MySQL接口实例。

        :param host: 数据库主机地址
        :param database: 数据库名称
        :param user: 用户名
        :param password: 密码
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connection = None

    def connect(self):
        """
        连接到MySQL数据库。
        """
        try:
            self.connection = pymysql.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                cursorclass=pymysql.cursors.DictCursor
            )
            print("Connected to MySQL database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")

    def disconnect(self):
        """
        断开与MySQL数据库的连接。
        """
        if self.connection and self.connection.open:
            self.connection.close()
            print("Disconnected from MySQL database")

    def execute_query(self, query, params=None):
        """
        执行SQL查询（如插入、更新、删除等）。

        :param query: SQL查询字符串
        :param params: 参数元组（用于防止SQL注入）
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            print("Query executed successfully")
        except Error as e:
            print(f"Error executing query: {e}")
        finally:
            if cursor:
                cursor.close()

    def fetch_data(self, query, params=None):
        """
        执行SQL查询并返回结果集。

        :param query: SQL查询字符串
        :param params: 参数元组（用于防止SQL注入）
        :return: 查询结果列表
        """
        cursor = None
        result = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            print("Data fetched successfully")
        except Error as e:
            print(f"Error fetching data: {e}")
        finally:
            if cursor:
                cursor.close()
        return result

    def insert_data(self, table, data):
        """
        向指定表中插入数据。

        :param table: 表名称
        :param data: 包含列名和值的字典
        """
        placeholders = ', '.join(['%s'] * len(data))
        columns = ', '.join(data.keys())
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.execute_query(sql, tuple(data.values()))

    def update_data(self, table, data, condition):
        """
        更新指定表中的数据。

        :param table: 表名称
        :param data: 包含列名和新值的字典
        :param condition: 更新条件（例如 "id = 1"）
        """
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        self.execute_query(sql, tuple(data.values()))

    def delete_data(self, table, condition):
        """
        从指定表中删除数据。

        :param table: 表名称
        :param condition: 删除条件（例如 "id = 1"）
        """
        sql = f"DELETE FROM {table} WHERE {condition}"
        self.execute_query(sql)

    def create_table(self, table_name, schema):
        """
        创建指定表。

        :param table_name: 表名称
        :param schema: 表的schema定义（例如 "id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255)"）
        """
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        self.execute_query(sql)

# 示例用法
if __name__ == "__main__":
    # 创建MySQL接口实例
    db_interface = MySQLInterface(host='localhost', database='your_database', user='root', password='StrongPass123!')

    # 连接到数据库
    db_interface.connect()

    # 创建表
    table_schema = """
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        position VARCHAR(255),
        salary DECIMAL(10, 2)
    """
    db_interface.create_table('employees', table_schema)

    # 插入数据
    employee_data = {'name': 'John Doe', 'position': 'Software Engineer', 'salary': 75000.00}
    db_interface.insert_data('employees', employee_data)

    # 查询数据
    select_query = "SELECT * FROM employees"
    employees = db_interface.fetch_data(select_query)
    for employee in employees:
        print(employee)

    # 更新数据
    update_data = {'position': 'Senior Software Engineer', 'salary': 85000.00}
    condition = "id = 1"
    db_interface.update_data('employees', update_data, condition)

    # 再次查询数据以验证更新
    updated_employees = db_interface.fetch_data(select_query)
    for employee in updated_employees:
        print(employee)

    # 删除数据
    delete_condition = "id = 1"
    db_interface.delete_data('employees', delete_condition)

    # 最后一次查询数据以验证删除
    final_employees = db_interface.fetch_data(select_query)
    for employee in final_employees:
        print(employee)

    # 断开数据库连接
    db_interface.disconnect()
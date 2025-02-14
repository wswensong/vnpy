import pymysql.cursors
from pymysql.err import Error
# import pymysql

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

    # def connect(self):
    #     """
    #     连接到MySQL数据库。
    #     """
    #     try:
    #         self.connection = pymysql.connect(
    #             host=self.host,
    #             database=self.database,
    #             user=self.user,
    #             password=self.password,
    #             cursorclass=pymysql.cursors.DictCursor
    #         )
    #         print("Connected to MySQL database")
    #     except Error as e:
    #         print(f"Error connecting to MySQL: {e}")
    def connect(self):
        """增强版连接方法"""
        try:
            if self.connection and self.connection.open:
                return True
                
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True  # 启用自动提交
            )
            # print(f"成功连接到MySQL数据库 {self.database}")
            return True
        except Exception as e:
            print(f"数据库连接失败: {str(e)}")
            self.connection = None
            raise RuntimeError("数据库连接失败") from e
    
    def check_connection(self):
        """检查并维持有效连接"""
        try:
            if not self.connection or not self.connection.open:
                self.connect()
            return True
        except Exception:
            return False

    def disconnect(self):
        """
        断开与MySQL数据库的连接。
        """
        if self.connection and self.connection.open:
            self.connection.close()
            # print("Disconnected from MySQL database")

    # def execute_query(self, query, params=None):
    #     """
    #     执行SQL查询（如插入、更新、删除等）。

    #     :param query: SQL查询字符串
    #     :param params: 参数元组（用于防止SQL注入）
    #     """
    #     cursor = None
    #     try:
    #         cursor = self.connection.cursor()
    #         cursor.execute(query, params)
    #         self.connection.commit()
    #         # print("Query executed successfully")
    #     except Error as e:
    #         print(f"Error executing query: {e}")
    #     finally:
    #         if cursor:
    #             cursor.close()

    def execute_query(self, query, params=None):
        """增强版查询执行"""
        if not self.check_connection():
            raise RuntimeError("数据库连接不可用")
            
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
            return True
        except pymysql.err.OperationalError as e:
            print(f"查询执行失败，尝试重连: {str(e)}")
            self.connect()
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
            return True
        except Exception as e:
            print(f"查询执行失败: {str(e)}")
            raise

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
            # print("Data fetched successfully")
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
        更新指定表中的数据，如果字段不存在则新增字段。

        :param table: 表名称
        :param data: 包含列名和新值的字典
        :param condition: 更新条件（例如 "id = 1"）
        """
        existing_fields = self.get_table_columns(table)
        new_fields = [field for field in data.keys() if field not in existing_fields]

        # Add new fields if they don't exist
        for field in new_fields:
            self.add_column_to_table(table, field)

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

    def get_table_columns(self, table_name):
        """
        获取指定表的所有字段名。

        :param table_name: 表名称
        :return: 字段名列表
        """
        query = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """
        results = self.fetch_data(query, (self.database, table_name))
        return [row['COLUMN_NAME'] for row in results]

    def add_column_to_table(self, table_name, column_name):
        """
        在指定表中添加一个新字段。

        :param table_name: 表名称
        :param column_name: 新字段名称
        """
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} TEXT"
        self.execute_query(sql)

    def smart_insert_data(self, table, data):
        """
        向指定表中插入数据，如果字段不存在则新建字段。

        :param table: 表名称
        :param data: 包含列名和值的字典
        """
        existing_fields = self.get_table_columns(table)
        new_fields = [field for field in data.keys() if field not in existing_fields]

        # Add new fields if they don't exist
        for field in new_fields:
            self.add_column_to_table(table, field)

        self.insert_data(table, data)

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

    # 插入一些初始数据
    initial_data = {'name': 'Alice'}
    db_interface.smart_insert_data('example_table', initial_data)

    # 尝试插入包含新字段的数据
    new_data = {'name': 'Bob', 'age': 30}
    db_interface.smart_insert_data('example_table', new_data)
    
    # 查询数据
    select_query = "SELECT * FROM employees"
    employees = db_interface.fetch_data(select_query)
    for employee in employees:
        print(employee)

    # 更新数据
    update_data = {'position': 'Senior Software Engineer', 'salary': 85000.00}
    condition = f"datetime = '{current_time}'"
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

    # 创建 users 表
    db_interface.create_table('users', 'id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255)')

    # 插入初始数据
    initial_data = {'name': 'Alice'}
    db_interface.insert_data('users', initial_data)

    # 查看插入的数据
    print(db_interface.fetch_data('SELECT * FROM users'))

    # 更新数据并动态添加新字段
    updated_data = {'name': 'Bob', 'email': 'bob@example.com'}
    db_interface.update_data('users', updated_data, 'id = 1')

    # 查看更新后的数据
    print(db_interface.fetch_data('SELECT * FROM users'))
    
    # 断开数据库连接
    db_interface.disconnect()
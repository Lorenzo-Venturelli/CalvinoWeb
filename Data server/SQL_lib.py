import pymysql
import pymssql
from concurrent.futures import ThreadPoolExecutor

# This class implement PyMySQL, for MySQL Server
class MySQL():
    def __init__(self, host, database, username, password):
        self.db = pymysql.connect(host=host,
                     user=username,
                     password=password,
                     db=database,
                     cursorclass=pymysql.cursors.DictCursor)

        print("Connected to MySQL database")
        self.pool = ThreadPoolExecutor(100)
        self.cursor = self.db.cursor()

    def query(self, query, args = tuple()):
        query = self.pool.submit(self.__runQuery, (str(query), args))
        return query.result()

    def __runQuery(self, query, args = tuple()):
        self.cursor.execute(str(query[0]), query[1])
        self.db.commit()
        return self.cursor.fetchall()

# This class implement PyMsSQL, for Microsoft SQL Server
class MsSQL():
    def __init__(self, server, username, password, database):
        self.db = pymssql.connect(server = str(server), user = str(username), password = str(password), database = str(database))
        self.db.autocommit(True)
        self.pool = ThreadPoolExecutor(1000)
        self.cursor = self.db.cursor()

    def query(self, query, args = tuple()):
        try:
            self.cursor.execute(query, args)
            self.db.commit()
        except Exception as reason:
            print(reason)
            return False

        try:
            result = self.cursor.fetchall()
        except Exception as reason:
            result = True
        return result
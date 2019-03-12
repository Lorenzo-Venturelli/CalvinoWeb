import pymysql
from concurrent.futures import ThreadPoolExecutor

class MySQL():
    def __init__(self, host, database, username, password):
        self.db = pymysql.connect(host=host,
                     user=username,
                     password=password,
                     db=database,
                     cursorclass=pymysql.cursors.DictCursor);

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

#db = MySQL(indirizzo, nome_db, nome_utente, password)

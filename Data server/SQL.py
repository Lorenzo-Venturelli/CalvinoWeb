import SQL_lib
from random import randint
import datetime
#riceve numero sensore, tipo dato, dato & inserici nel DB + timestamp e numero casuale
#richiesta di dati per sensore , per tipo o per sensore/tipo o per range di data (in ogni caso ritorna sempre la data)

class CalvinoDB():
    def __init__(self, databaseAddress, databaseName, user, password):
        self.__dbAddress = databaseAddress
        self.__dbName = databaseName
        self.__dbUser = user
        self.__dbPass = password
        self.db = SQL_lib.MySQL(self.__dbAddress, self.__dbName, self.__dbName, self.__dbPass)

    def __randomN(self, digits):
        range_start = 10 **(digits - 1)
        range_end = (10 ** digits) - 1
        return randint(range_start, range_end)

    def insert(self, tipo, sensore, valore): #2019-03-12 11:57:44.937819
        try:
            self.db.query("INSERT INTO %s VALUES (%s, %s, %s, %s);", (tipo, self.__randomN(digits = 16), sensore, datetime.datetime.utcnow() + datetime.timedelta(hours=+1), valore))
        except Exception:
            return False

        return True

    #def request(self, dataI, dataF, sensore = None, tipo = None):
     #   if (sensore == None):
      #      if (tipo == None):

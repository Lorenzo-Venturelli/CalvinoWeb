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
        self.db = SQL_lib.MsSQL(server = self.__dbAddress, database = self.__dbName, username = self.__dbUser, password = self.__dbPass)

    def __randomN(self, digits):
        range_start = 10 **(digits - 1)
        range_end = (10 ** digits) - 1
        return randint(range_start, range_end)

    def insert(self, tipo, sensore, valore):
        ID = self.__randomN(digits = 16)
        timestamp = str(datetime.datetime.utcnow() + datetime.timedelta(hours=+1))
        timestamp = "\'" + timestamp[:-7]  + "\'"   # Format timestamp in MS SQL 'datetime' format
        queryResult = self.db.query('''INSERT INTO ''' + str(tipo) + ''' VALUES (''' + str(ID) + ''', ''' + str(sensore) + ''', ''' + str(timestamp) + ''', ''' + str(valore) + ''')''')
        #queryResult = self.db.query("INSERT INTO %s VALUES (%s, %s, %s, %s)", (str(tipo).strip(), str(ID).strip(), str(sensore).strip(), str(timestamp), str(valore).strip()))

        if queryResult == True:         # Query succeded without output
            return True
        elif queryResult == False:      # Query failed
            return False
        else:                           # Query succeded with output
            return True

    #def request(self, dataI, dataF, sensore = None, tipo = None):
     #   if (sensore == None):
      #      if (tipo == None):

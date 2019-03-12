import SQL_lib
from random import randint
import datetime
#riceve numero sensore, tipo dato, dato & inserici nel DB + timestamp e numero casuale
#richiesta di dati per sensore , per tipo o per sensore/tipo o per range di data (in ogni caso ritorna sempre la data)

class CalvinoDB():
    def __init__(self):
        self.db = SQL_lib.MySQL("172.20.16.4", "CalvinoDB", "root", "fermi3f27")

    def random_N(n):#numero random di n cifre
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

    def insert(self, tipo, sensore, valore): #2019-03-12 11:57:44.937819
        try:
            self.db.query("INSERT INTO %s VALUES (%s, %s, %s, %s);", (tipo, self.random_N(16), sensore, datetime.datetime.utcnow() + datetime.timedelta(hours=+1), valore))
        except Exception:
            return False
        return True

    def request(self, dataI, dataF, sensore = None, tipo = None):
        if (sensore == None):
            if (tipo == None):

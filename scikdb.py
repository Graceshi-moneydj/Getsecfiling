import csv

class Object(object):
    pass

class SCIK:
    def __init__(self, symbol, cik, currency):
        self.symbol = symbol
        self.cik = cik
        self.currency = currency

class SCIKDB:
    cikmap = Object()
    symbolmap = Object()
    list = []
    def load(self, filename):
        with open(filename, 'r') as file:
            csvreader=csv.reader(file)
            for row in csvreader:
                scik = SCIK(row[0], row[1], 'US') #[symbol, cik, exchange]
                self.list.append(scik)
                setattr(self.symbolmap, row[0], scik)
                setattr(self.cikmap, row[1], scik)
            
    def get_SCIK(self, symbol)->SCIK:
        return getattr(self.symbolmap, symbol);  

    def get_Symbol(self, cik)->str:
        scik = getattr(self.cikmap, cik)
        if scik is not None:
            return scik.symbol
        
        return ''
                
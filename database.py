import sqlite3
import getpass
import time

class Database:
    
    laptimesDb = '\dirtrally-laptimes.db'
    
    def __init__(self, approot):
        self.approot = approot
        self.db = self.checkSetup(approot)
    
    def checkSetup(self, approot):
        try:
            conn = sqlite3.connect(approot + '/dirtrally-lb.db')
            db = conn.cursor()
            return db
        except (Exception) as exc:
            # TODO Set it up with tracks.sql and cars.sql
            print("Error connecting to database:", exc)

    def initializeLaptimesDb(self):
        try:
            lapconn = sqlite3.connect(self.approot + self.laptimesDb)
            lapdb = lapconn.cursor()
            lapdb.execute('SELECT user FROM user;')
            res = lapdb.fetchall()
            userArray = res[0]
        except (Exception) as exc:
            try:
                print("First run, setting up recording tables")
                lapdb.execute('CREATE TABLE laptimes (Track INTEGER, Car INTEGER, Timestamp INTEGER, Time REAL);')
                lapdb.execute('CREATE TABLE user (user TEXT);')
                userId = self.createUserId()
                lapdb.execute('INSERT INTO user VALUES (?)', (userId, ))
                lapconn.commit()
                lapdb.execute('SELECT user FROM user;')
                res = lapdb.fetchall()
                userArray = res[0]
            except (Exception) as exc:
                print("Error initializing " + self.laptimesDb, exc)
        finally:
            lapconn.close()
        
        return userArray
    
    def createUserId(self):
        user = getpass.getuser()
        user = 'defaultuser' if (user == None) else user
        epoch = int(time.time())
        return str(user) + str(epoch)

    def loadTracks(self, tracklength):
        self.db.execute('SELECT id, name, startz FROM Tracks WHERE abs(length - ?) < 0.001', (tracklength,))
        return self.db.fetchall()

    def loadCars(self, rpm, max_rpm):
        # Some more delta allowed for startrpm as 2nd Pikes Peak run seems to simulate worn/warmed up engine
        self.db.execute('SELECT id, name FROM cars WHERE abs(maxrpm - ?) < 0.01 AND abs(startrpm - ?) < 2.0', (max_rpm, rpm))
        return self.db.fetchall()

    def recordResults(self, track, car, timestamp, laptime):
        try:
            lapconn = sqlite3.connect(self.approot + self.laptimesDb)
            lapdb = lapconn.cursor()
            lapdb.execute('INSERT INTO laptimes (Track, Car, Timestamp, Time) VALUES (?, ?, ?, ?)', (track, car, timestamp, laptime))
            lapconn.commit()
            lapconn.close()
        except (Exception) as exc:
            print("Error connecting to database:", exc)
            
    def getUpdateStatements(self, timestamp, cars):
        result = []
        for index in cars:
            result.append('UPDATE laptimes SET Car=%s WHERE Timestamp="%s";' % (index, timestamp))
        
        return result
    
    def getCarName(self, car):
        self.db.execute('SELECT name FROM cars WHERE id = ?', (car,))
        return self.db.fetchone()[0]
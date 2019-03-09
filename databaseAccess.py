import time

class DatabaseAccess:
    
    def __init__(self, database):
        self.database = database
    
    def identifyTrack(self, z, tracklength):
        tracks = self.database.loadTracks(tracklength)

        if (len(tracks) == 0):
            print("Failed to identify track: %s" % (str(tracklength)))
            return []
        
        elif (len(tracks) == 1):
            index, name, startz = tracks[0]
            print("TRACK: %s" % str(name))
            return index
        
        elif (len(tracks) > 1):
            for index, name, startz in tracks:
                # TODO #2 This check must consider identical Pikes Peak tracks properly! 
                if index < 1000 and abs(z - startz) < 50:
                    print("TRACK: %s (Z: %s)" % (str(name), str(z)))
                    return index
        
            print("Ambiguous track data, %s matches: %s (Z: %s)" % (len(tracks), str(tracklength), str(z)))
            return list(index for (index, name, startz) in tracks)
    
    def logCar(self, rpm, max_rpm, name):
        print("CAR: %s (%s - %s)" % (name, str(rpm), str(max_rpm)))

    def identifyCar(self, rpm, max_rpm):
        cars = self.database.loadCars(rpm, max_rpm)
        if (len(cars) == 0):
            print("Failed to identify car: %s - %s" % (str(rpm), str(max_rpm)))
            return []
        
        elif (len(cars) == 1):
            index, name = cars[0]
            self.logCar(rpm, max_rpm, name)
            return index
        
        else:
            print("Ambiguous car data, %s matches: %s - %s" % (len(cars), str(rpm), str(max_rpm)))
            return list(index for (index, name) in cars)


    def printCarUpdates(self, car, timestamp):
        updates = self.database.getCarUpdateStatements(timestamp, car)
        print("Please update the recorded laptimes according to the correct car:")
        for index, update in enumerate(updates):
            elementId = car[index]
            carName = self.database.getCarName(elementId)
            print("%s ==> %s" % (carName, update))


    def printTrackUpdates(self, track, timestamp):
        updates = self.database.getTrackUpdateStatements(timestamp, track)
        print("Please update the recorded laptimes according to the correct track:")
        for index, update in enumerate(updates):
            elementId = track[index]
            trackName = self.database.getTrackName(elementId)
            print("%s ==> %s" % (trackName, update))

    def recordResults(self, track, car, laptime):
        timestamp = time.time()
        self.database.recordResults(self.identify(track), self.identify(car), timestamp, laptime)
        
        if isinstance(car, (list,)):
            self.printCarUpdates(car, timestamp)
                
        if isinstance(track, (list,)):
            self.printTrackUpdates(track, timestamp)

    def identify(self, element):
        return element if isinstance(element, int) else -1


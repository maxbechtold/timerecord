from .ambiguousResultHandler import AmbiguousResultHandler
from .database import Database
from .databaseAccess import DatabaseAccess
from .gearTracker import GearTracker
from .log import getLogger
from .progressTracker import ProgressTracker
from .respawnTracker import RespawnTracker
from .speedTracker import SpeedTracker
from .timeTracker import TimeTracker

goLineProgress = 0.0
completionProgress = 0.999

logger = getLogger(__name__)

class StatsProcessor():

    def __init__(self, speed_unit, approot):
        self.speed_unit = speed_unit
        self.speed_modifier = speed_unit == 'mph' and 0.6214 or 1
        self.track = 0
        self.car = 0

        self.ambiguousResultHandler = AmbiguousResultHandler(Database.laptimesDbName)
        self.database = self.updateResources(approot)

        self.databaseAccess = DatabaseAccess(self.database, self.ambiguousResultHandler)
        self.userArray = self.database.initializeLaptimesDb()
        self.initTrackers()

    def updateResources(self, approot):
        self.ambiguousResultHandler.cleanUp(approot)
        database = Database(approot).setup()
        return database

    def formatTopSpeed(self):
        topSpeed_kmh = self.speedTracker.getTopSpeed() * 3.6
        return '%.1f' % (topSpeed_kmh * self.speed_modifier,)

    def formatLapTime(self, laptime):
        return '%.2f' % (laptime,)

    def printResults(self, laptime):
        dbAccess = self.databaseAccess
        logger.debug("%s.%s.%s.time:%s|s", self.userArray[0], dbAccess.identify(self.track), dbAccess.identify(self.car), self.formatLapTime(laptime))
        logger.debug("%s.%s.%s.topspeed:%s|%s", self.userArray[0], dbAccess.identify(self.track), dbAccess.identify(self.car), self.formatTopSpeed(), self.speed_unit)
        logger.info("Completed stage in %ss.", self.formatLapTime(laptime))

    def showCarControlInformation(self):
        if isinstance(self.car, (list,)):
            for car in self.car:
                logger.info(self.databaseAccess.describeCarInterfaces(car))
        else:
            logger.info(self.databaseAccess.describeCarInterfaces(self.car))

    def allZeroStats(self, stats):
        return stats.count(0) == len(stats)

    def statsWithTelemetry(self, stats):
        return not self.allZeroStats(stats)

    def stageAborted(self):
        timeDelta = self.timeTracker.getTimeDelta()
        isAborted = self.respawnTracker.isRestart() or timeDelta < 0
        return isAborted

    def handleStats(self, stats):
        if self.statsWithTelemetry(stats):
            self.respawnTracker.track(stats)
            self.timeTracker.track(stats)
            self.progressTracker.track(stats)
            self.gearTracker.track(stats)
            self.speedTracker.track(stats)

        lap = self.progressTracker.getLap()
        stageProgress = self.progressTracker.getProgress()

        self.handleGameState(self.stageAborted(), self.inStage(), lap, stageProgress, stats)

    def resetRecognition(self):
        self.track = 0
        self.car = 0
        self.initTrackers()

    def inStage(self):
        return self.track != 0 and self.car != 0

    def initTrackers(self):
        self.respawnTracker = RespawnTracker()
        self.timeTracker = TimeTracker()
        self.gearTracker = GearTracker(self.respawnTracker)
        self.progressTracker = ProgressTracker()
        self.speedTracker = SpeedTracker()

    def startStage(self, stats):
        dbAccess = self.databaseAccess

        track_z = stats[6]
        track_length = self.progressTracker.getTrackLength()
        self.track = dbAccess.identifyTrack(track_z, track_length)

        car_data = stats[63:66] # max_rpm, idle_rpm, top_gear
        self.car = dbAccess.identifyCar(*tuple(car_data))

        logger.debug("%s.%s.%s.started", self.userArray[0], dbAccess.identify(self.track), dbAccess.identify(self.car))

        self.showCarControlInformation()

    def finishStage(self, stats):
        laptime = stats[62]
        self.databaseAccess.recordResults(self.track, self.car, laptime, self.formatTopSpeed())
        self.printResults(laptime)

    def finishedDR2TimeTrial(self, stats, trackProgess):
        return trackProgess >= completionProgress and self.allZeroStats(stats)

    def handleGameState(self, isAborted, inStage, lap, stageProgress, stats):
        if inStage and (lap == 1 or self.finishedDR2TimeTrial(stats, stageProgress)):
            self.finishStage(stats)
            self.resetRecognition()

        elif isAborted:
            self.resetRecognition()

        elif self.statsWithTelemetry(stats) and stageProgress <= goLineProgress and not inStage:
            self.startStage(stats)
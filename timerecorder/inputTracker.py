from enum import Enum
from .log import getLogger, VERBOSE

logger = getLogger(__name__)

steering_offset = 0.2
throttle_offset = 0.5

class Signal(Enum):
    THROTTLE_LEFT = 1
    THROTTLE_RIGHT = 2

# Steer (left-neutral-right): -1.0..1.0
# Throttle (no-full): 0.0..1.0
class InputTracker():

    def __init__(self, speedTracker, notify):
        self.speedTracker = speedTracker
        self.notify = notify
        self.input = None
        self.signal = None
        self.enabled = True

        self.toggle = False

    # TODO #41 Must ignore approaching start line (DR1), wait for brake: 1.0, speed: 0 (car stops)?
    def hasLaunched(self):
        return self.speedTracker.getTopSpeed() > 1.0

    def getSignal(self):
        return self.signal

    def isSignalLeft(self, throttle, steer):
        return steer < -steering_offset and throttle > throttle_offset

    def isSignalRight(self, throttle, steer):
        return steer > steering_offset and throttle > throttle_offset

    def track(self, stats):
        throttle, steer = (stats[29:31])

        # #41 Debug
        brake = stats[31]
        self.toggle = not self.toggle
        if self.toggle:
            print('brake: %s, speed: %s' % (brake, self.speedTracker.getSpeed()))

        if not self.enabled:
            return

        if self.hasLaunched():
            self.enabled = False
            logger.debug('LAUNCHED')
            return

        anySignal = self.isSignalLeft(throttle, steer) or self.isSignalRight(throttle, steer)
        if self.input is not None and not anySignal:
            self.signal = self.input
            self.input = None
            logger.debug('signal received: %s', self.signal)

        if self.input is not None:
            return

        if self.isSignalLeft(throttle, steer):
            self.input = Signal.THROTTLE_LEFT
            logger.log(VERBOSE, 'engage THROTTLE turning LEFT')
            self.notify()

        if self.isSignalRight(throttle, steer):
            self.input = Signal.THROTTLE_RIGHT
            logger.log(VERBOSE, 'engage THROTTLE turning RIGHT')
            self.notify()

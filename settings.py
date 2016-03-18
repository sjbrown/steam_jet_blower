from os.path import curdir
from os import name
if name == 'posix':
	TMPDIR = '/tmp'
else:
	TMPDIR = curdir

bubbleRate80Degrees = 4*1000
bubbleRate100Degrees = 2*1000
bubbleRate190Degrees = .5*1000
bubbleRate500Degrees = .3*1000

bubbleFormingTime = 2*1000
bubbleCeilingTime = 2*1000

bladderCapacity = 50
bladderMaxPower = 3
bladderOCTime = 5000 # how long the bladder is allowed to stay over capacity

stripeStartOpacityviolet = 15 
stripeStartOpacityblue   = 15
stripeStartOpacitygreen  = 15
stripeStartOpacityyellow = 15
stripeStartOpacityorange = 15
stripeStartOpacityred    = 15
stripeLowOpacity   = 10 
stripeBonusOpacity = 30 
#stripeBonusOpacity = 50
stripeOpacityLeakTime = 6*1000

geyserLifetime= 2*1000

purseCapacity = 20
purseIncrement = 4

fireDuration = 20*1000
fireStrikeLimit = 0.4*1000
fireMatchCost = 50

windGustTimeMin = 1*1000
windGustTimeMax = 10*1000
windSpinningMin = 1*1000
windSpinningMax = 10*1000
windTemperature = 101

waterWheelRepairCost = 200
waterWheelDuration = 30*1000
waterWheelAccelerationDuration = 5*1000
waterWheelTemperature = 101
waterWheelAcceleratedTemperature = 191

nukeTemperature = 501
nukeFuelCost = 400
nukeDuration = 12*1000


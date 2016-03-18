from log import log
import pygame
import mvcState
from pygame.sprite import Sprite

from random import Random
rng = Random()

from settings import *
import settings

#-----------------------------------------------------------------------------
class CursorComposer:
	def __init__(self, xlens, ylens):
		self.alreadyMovedInThisFrame = False
		self.cursorImg = load_png( 'heater_cursor.png' )
		self.cursorRect = self.cursorImg.get_rect()
		self.cursorIndex = 0

		self.xlens = xlens
		self.ylens = ylens

		self.BeginLoopCallback = None
		self.EndLoopCallback = None

	def BeginUpdate(self):
		self.alreadyMovedInThisFrame = False

	def Update(self, origImg):
		image = origImg.convert_alpha()

		x = self.xlens[self.cursorIndex]
		y = self.ylens[self.cursorIndex]
		self.cursorRect.topleft = ( x, y )
		image.blit( self.cursorImg, self.cursorRect.topleft )

		return image

	def OnMouseMove( self, translatedPos ):
		innerRect = self.cursorRect.inflate(-1,-1)
		if innerRect.collidepoint( translatedPos ):
			self.MouseInCursor()

	def MouseInCursor( self ):
		if self.alreadyMovedInThisFrame:
			return

		self.alreadyMovedInThisFrame = True

		if self.cursorIndex == 0:
			if self.BeginLoopCallback:
				self.BeginLoopCallback()

		self.cursorIndex += 1
		self.cursorIndex %= len( self.xlens )

		if self.cursorIndex == 0:
			if self.EndLoopCallback:
				self.EndLoopCallback()



#-----------------------------------------------------------------------------
class Bladder(Sprite):
	def __init__(self):
		Sprite.__init__(self)
		self.fillingImgs = [
		                    load_png( 'bladder00.png' ),
		                    load_png( 'bladder01.png' ),
		                    load_png( 'bladder02.png' ),
		                    load_png( 'bladder03.png' ),
		                    load_png( 'bladder04.png' ),
		                   ]
		self.tooFullImg = load_png( 'bladder_toofull.png' )
		self.ventImg = self.tooFullImg
		self.shootImg = load_png( 'bladder_shoot.png' )
		self.image = self.fillingImgs[0]
		self.rect = self.image.get_rect()

		self.originalMidBottom = self.rect.midbottom
		self.dirty = 1

		self.capacity = settings.bladderCapacity
		self.numBubbles = 0
		self.isShooting = False
		self.isVenting = False
		self.overCapacityCounter = 0
		self.tooFullAnimCounter= 0
		self.squeezeFactor = 0
		self.maxPower = settings.bladderMaxPower

		self.tooFullAnim = [ (2,0), (-2,0) ]
		self.tooFullAnimIndex = 0

		controller = mvcState.GetController()
		controller.gameEventListeners.append( self )
		controller.mouseListeners.append( self )

	def kill( self ):
		Sprite.kill( self )
		controller = mvcState.GetController()
		controller.gameEventListeners.remove( self )
		controller.mouseListeners.remove( self )

	def FixBottom( self, fixedBottom ):
		if type(fixedBottom[0]) != int or type(fixedBottom[1]) != int:
			raise Exception( "Fix Bottom Failure" )
		self.originalMidBottom = fixedBottom

	def update( self, timeChange ): 
		if not self.dirty:
			return

		if self.isVenting:
			#log.debug( 'bladder is venting' )
			controller = mvcState.GetController()
			self.image = self.ventImg
			self.rect = self.image.get_rect()
			self.rect.midbottom = self.originalMidBottom

			power = min( self.numBubbles, self.maxPower )
			height = rng.randint(0,5)
			controller.GameEvent( 'BladderVent', power,height )
			self.numBubbles -= power

			if self.numBubbles < 1:
				self.isVenting = False
				controller.GameEvent( 'BladderVentStop' )

			self.dirty = 1

		elif self.isShooting:
			#log.debug( 'bladder is shooting' )
			controller = mvcState.GetController()
			self.image = self.shootImg
			self.rect = self.image.get_rect()
			self.rect.midbottom = self.originalMidBottom

			power = min( self.numBubbles, self.maxPower )
			height = self.squeezeFactor
			controller.GameEvent( 'BladderShoot', power,height )
			self.numBubbles -= power

			if self.numBubbles < 1:
				self.isShooting = False
				controller.GameEvent( 'BladderShootStop' )

			self.dirty = 1

		elif not self.numBubbles > self.capacity:
			fullFraction = float(self.numBubbles) / self.capacity
			#log.debug( 'fullfraction'+str(fullFraction) )
			index = min( int( len(self.fillingImgs)*fullFraction ),
			             len(self.fillingImgs)-1 )
			#log.debug( 'index'+str(index) )
			self.image = self.fillingImgs[index]
			self.rect = self.image.get_rect()
			self.rect.midbottom = self.originalMidBottom

			self.dirty = 0

		else: #bubbles > capacity
			self.overCapacityCounter += timeChange
			self.tooFullAnimCounter += timeChange
			if self.overCapacityCounter > settings.bladderOCTime:
				self.isVenting = True
				self.overCapacityCounter = 0
			else:
				self.TooFullAnimate()

			self.dirty = 1

	def TooFullAnimate(self):
		if self.tooFullAnimCounter < 200:
			return
		self.tooFullAnimCounter = 0

		controller = mvcState.GetController()
		controller.GameEvent( 'BladderVentingImminent' )

		if self.image == self.tooFullImg:
			img = self.fillingImgs[len(self.fillingImgs)-1]
		else:
			img = self.tooFullImg
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midbottom = self.originalMidBottom

		self.rect.move_ip( *self.tooFullAnim[self.tooFullAnimIndex] )

		self.tooFullAnimIndex += 1
		self.tooFullAnimIndex %= len(self.tooFullAnim)


	def OnBubbleHitCeiling(self):
		self.numBubbles += 1
		self.dirty = 1

	def OnMouseMove( self, event ): 
		if not self.isShooting:
			return
		distFromCenter = min( abs(event.pos[0]-self.rect.centerx), 199 )
		self.squeezeFactor = int( distFromCenter*(6.0/200) )
		#log.debug( 'set squeezefactor to '+ str( self.squeezeFactor ) )
		self.dirty = 1
			


	def OnMouseDown( self, pos ): 
		if not self.rect.collidepoint( pos ):
			return
		if self.numBubbles < 1:
			return
		self.squeezeFactor = 0
		self.isShooting = True
		controller = mvcState.GetController()
		controller.GameEvent( 'BladderShootStart' )
		self.dirty = 1

	def OnMouseUp( self, pos ): 
		if self.isShooting:
			self.isShooting = False
			controller = mvcState.GetController()
			controller.GameEvent( 'BladderShootStop' )
			self.dirty = 1
	


import precomputed_circle
from utils import load_png

#-----------------------------------------------------------------------------
class Bubble(Sprite):
	def __init__(self, ceilingY):
		Sprite.__init__(self)
		self.formingImg= load_png( 'bubble_forming.png' )
		self.risingImg= load_png( 'bubble_rising.png' )
		self.rect = self.formingImg.get_rect()
		self.image = self.formingImg

		self.ceilingY = ceilingY
		self.isAtCeiling = False
		self.birthTimeCounter = 0
		self.nextJiggleCounter = 500
		self.deathCounter = 0

	def Rise( self ):
		#log.debug( 'bubble starts rising' )
		self.image = self.risingImg
		tmpRect = self.risingImg.get_rect()
		tmpRect.midbottom = self.rect.midbottom
		self.rect = tmpRect

	def update( self, timeChange ): 
		self.birthTimeCounter += timeChange

		if self.birthTimeCounter > settings.bubbleFormingTime \
		  and self.image == self.formingImg:
			self.Rise()

		elif self.image == self.risingImg and not self.isAtCeiling:
			self.rect.y = self.rect.y-1
			if self.rect.top < self.ceilingY:
				controller = mvcState.GetController()
				controller.GameEvent( "BubbleHitCeiling" )
				self.isAtCeiling = True
				self.rect.top = self.ceilingY
				self.deathCounter = self.birthTimeCounter + \
				                    settings.bubbleCeilingTime

		if self.birthTimeCounter > self.nextJiggleCounter:
			self.rect.x += rng.randint(-1,1)
			self.nextJiggleCounter += 500

		if self.isAtCeiling \
		  and self.birthTimeCounter > self.deathCounter:
			#log.debug( 'killing bubble' )
		  	self.kill()

#-----------------------------------------------------------------------------
class Cloud(Sprite):
	def __init__(self):
		Sprite.__init__(self)
		self.stableImg = load_png( 'cloud.png' )
		self.image = self.stableImg
		self.rect = self.image.get_rect()

		self.jiggleCounter = 1500
		self.jiggles = [ (4,0), (-4,0), (-1,3), (-2,-4), (3,1) ]
		self.jiggleIndex = 0

		self.dripMoves = [ (0,3), (0,2), (0,2), 
		                   (0,1), (0,1), (0,1), (0,1), 
		                   (0,-3), 
		                   (0,-3), 
		                   (0,-3), 
		                   (0,-1), 
		                   (0,-1), 
		                 ]
		self.dripIndex = 0
		self.isDripping = False
		self.dropColor = None

	def Jiggle( self ): 
		self.jiggleCounter = 1500
		self.rect.move_ip( self.jiggles[self.jiggleIndex] )
		self.jiggleIndex += 1
		self.jiggleIndex %= len( self.jiggles )

	def StartDrip( self, colorName ): 
		self.isDripping = True
		self.dropColor = colorName

	def Drip( self ): 
		self.rect.move_ip( self.dripMoves[self.dripIndex] )
		self.dripIndex += 1
		self.dripIndex %= len( self.dripMoves )
		if self.dripIndex == 7:
			controller = mvcState.GetController()
			controller.GameEvent( 'LaunchDrop', self.rect.center,
			                                    self.dropColor )
		if self.dripIndex == 0:
			self.isDripping = False

	def update( self, timeChange ): 
		if not self.isDripping:
			self.jiggleCounter -= timeChange
			if self.jiggleCounter < 0:
				self.Jiggle()

		else:
			self.Drip()

from utils import change_alpha#, change_alpha_mult
from change_transparency import change_alpha_mult

#-----------------------------------------------------------------------------
class Stripe(Sprite):
	def __init__(self, name, height):
		Sprite.__init__(self)

		self.height = height
		self.name = name
		self.shouldLeak = True
		start_opa = getattr( settings, 'stripeStartOpacity'+name )
		self._opacity= start_opa
		self.hiOpacityLimit = 100
		self.bonusOpacityLimit = settings.stripeBonusOpacity
		self.lowOpacityLimit = settings.stripeLowOpacity
		self.opacityImgStep = 5

		self.fullImg= load_png( 'stripe_'+name+'_full.png' )
		self.rect = self.fullImg.get_rect()

		numImages = (self.hiOpacityLimit - self.lowOpacityLimit ) \
		            / self.opacityImgStep

		self.allImages = []
		import os.path
		for i in range( numImages ):
			alpha = self.lowOpacityLimit+ (self.opacityImgStep*i)
			filename = os.path.join( settings.TMPDIR,
			               'stripe'+ self.name + str(alpha) +'.tga')
			try:
				img = pygame.image.load(filename)
				if img == None:
					raise Exception("WTF")
			except Exception, e:
				log.debug( 'could not load cached stripe' )
				log.debug( e )
				img = self.fullImg.convert_alpha()
				change_alpha_mult( img, alpha )
				img.unlock()
				try:
					pygame.image.save( img, filename )
				except Exception, e:
					log.debug( 'could not save stripe' )
					log.debug( e )

			self.allImages.append( img )
		self.ComposeImg()

		self.lastChangeCounter = 0

		controller = mvcState.GetController()
		controller.gameEventListeners.append( self )

		self.dirty = 1

	def kill( self ): 
		log.debug( 'stripe getting killed' )
		Sprite.kill(self)
		controller = mvcState.GetController()
		controller.gameEventListeners.remove(self)

	def OpacityChange( self, change ): 
		#log.debug( self.name + 'stripe changes opacity'+ str(change) +str(self._opacity) )
		controller = mvcState.GetController()
		self._opacity += change
		if self._opacity >= self.hiOpacityLimit:
			self._opacity = self.hiOpacityLimit
			self.shouldLeak = False
			controller.GameEvent( 'StripeHitMaxOpacity', self )
		if self._opacity < self.lowOpacityLimit:
			self._opacity = self.lowOpacityLimit
		if self._opacity > self.bonusOpacityLimit:
			controller.GameEvent( 'StripeAtBonusOpacity', self )
		self.dirty = 1

	def ComposeImg( self ): 
		if self._opacity == self.hiOpacityLimit:
			index = len(self.allImages)-1
		else:
			step = self.opacityImgStep
			delta = self._opacity - self.lowOpacityLimit
			index= ( delta/step )
		self.image = self.allImages[ index ]
		if self.image == None:
			print "WTF"
			raise Exception("WTF -image")
		
	def update( self, timeChange ): 
		self.lastChangeCounter += timeChange
		if self.dirty:
			self.ComposeImg()
			self.lastChangeCounter = 0
			self.dirty = 0

		elif self.lastChangeCounter > settings.stripeOpacityLeakTime:
			self.lastChangeCounter = 0
			if self.shouldLeak:
				self.OpacityChange( -1 )
				self.ComposeImg()

	def OnBladderShoot(self, power, height):
		if height != self.height:
			return
		self.OpacityChange( power )

	def OnBladderVent(self, power, height):
		if height != self.height:
			return
		self.OpacityChange( power )

#-----------------------------------------------------------------------------
class Geyser(Sprite):
	def __init__(self, height="tall"):
		Sprite.__init__(self)

		if height == "tall":
			self.image = load_png( 'geyser_tall.png' )
		else:
			self.image = load_png( 'geyser_short.png' )
		self.rect = self.image.get_rect()

		self.jiggleCounter = 200
		self.lifeCounter = settings.geyserLifetime

	def Jiggle( self ): 
		self.jiggleCounter = 200
		self.rect.x += rng.randint(-1,1)

	def update( self, timeChange ): 
		self.jiggleCounter -= timeChange
		self.lifeCounter -= timeChange
		if self.jiggleCounter < 0:
			self.Jiggle()
		if self.lifeCounter < 0:
			self.kill()


#-----------------------------------------------------------------------------
class Lock(Sprite):
	def __init__(self):
		Sprite.__init__(self)

		self.image = load_png( 'lock.png' )
		self.rect = self.image.get_rect()

	def update( self, timeChange ): 
		return

#-----------------------------------------------------------------------------
class InstructionSpin(Sprite):
	def __init__(self):
		Sprite.__init__(self)

		self.images = [load_png( 'instruction_spin00.png' ),
		               load_png( 'instruction_spin01.png' ) ]
		self.image = self.images[0]
		self.rect = self.image.get_rect()

		self.timer = 200
		self.imgIndex = 0

	def update( self, timeChange ): 
		self.timer -= timeChange
		if self.timer < 0:
			self.timer = 200
			self.imgIndex += 1
			self.imgIndex %= len(self.images)
			self.image = self.images[self.imgIndex]

#-----------------------------------------------------------------------------
class InstructionPress(InstructionSpin):
	def __init__(self):
		Sprite.__init__(self)

		self.images = [load_png( 'instruction_press00.png' ),
		               load_png( 'instruction_press01.png' ) ]
		self.image = self.images[0]
		self.rect = self.image.get_rect()

		self.timer = 200
		self.imgIndex = 0



#-----------------------------------------------------------------------------
class Drop(Sprite):
	def __init__(self, colName, startPos):
		Sprite.__init__(self)

		self.colorName = colName
		self.image = load_png( 'drop_'+self.colorName+'.png' )
		self.rect = self.image.get_rect()
		self.rect.midtop = startPos

		controller = mvcState.GetController()
		controller.GameEvent( 'DropBirth', self )

	def update( self, timeChange ): 
		bucketY = 330

		self.rect.move_ip( 0,4 )

		if self.rect.bottom >= bucketY:
			controller = mvcState.GetController()
			controller.GameEvent( 'DropHitsBucket', self.colorName )
			self.kill()

#-----------------------------------------------------------------------------
class Purse:
	def __init__(self, colorName):
		self.amount = 0
		self.capacity = settings.purseCapacity
		self.colorName = colorName

		controller = mvcState.GetController()
		controller.gameEventListeners.append( self )

	def OnDropHitsBucket( self, colorName ):
		if colorName != self.colorName:
			return

		self.amount += settings.purseIncrement
		#log.debug( 'drop hit the bucket'+ colorName )
		controller = mvcState.GetController()
		if self.amount == self.capacity:
			controller.GameEvent( "PurseFull", colorName )
		elif self.amount > self.capacity:
			controller.GameEvent( "DropOverCapacity", colorName )
			self.amount = self.capacity

	def OnBoughtNuke( self ):
		if self.colorName == 'orange':
			self.amount = 0
	def OnBoughtFire( self ):
		if self.colorName == 'yellow':
			self.amount = 0
	def OnBoughtWind( self ):
		if self.colorName == 'green':
			self.amount = 0
	def OnBoughtWaterWheel( self ):
		if self.colorName == 'blue':
			self.amount = 0
	def OnBoughtSolar( self ):
		if self.colorName == 'violet':
			self.amount = 0



#-----------------------------------------------------------------------------
from pygame import Surface, SRCALPHA
class MoneyWidget(Sprite):
	def __init__(self, amount, showDollar=False):
		Sprite.__init__(self)
		self.amount = amount
		self.capacity = 9999
		self.showDollar = showDollar

		self.dollarImg = load_png( 'alpha_dollar.png' )
		self.imgNums = [
		                load_png( 'alpha_0.png' ),
		                load_png( 'alpha_1.png' ),
		                load_png( 'alpha_2.png' ),
		                load_png( 'alpha_3.png' ),
		                load_png( 'alpha_4.png' ),
		                load_png( 'alpha_5.png' ),
		                load_png( 'alpha_6.png' ),
		                load_png( 'alpha_7.png' ),
		                load_png( 'alpha_8.png' ),
		                load_png( 'alpha_9.png' ),
		               ]

		self.image = self.dollarImg.convert_alpha() #copy it
		self.rect = self.image.get_rect()

		self.ComposeImg()
		self.dirty = 1

		controller = mvcState.GetController()
		controller.gameEventListeners.append( self )

	def ComposeImg( self ): 
		strNum = str( self.amount )
		self.image = Surface( (28*(2+len(strNum)), 28), SRCALPHA, 32 )
		self.image.fill( (0,0,0,0) )
		
		if self.showDollar:
			self.image.blit( self.dollarImg, (0,0) )
			x = 24
		else:
			x = 0
		for char in strNum:
			index = int( char )
			self.image.blit( self.imgNums[index], (x,0) )
			x += 24

		self.rect.width = self.image.get_rect().width

	def update( self, timeChange ): 
		if self.dirty:
			self.ComposeImg()

	def ChangeMoney( self, change ): 
		self.amount += change
		if self.amount > self.capacity:
			self.amount = self.capacity
		self.dirty = 1

	def OnFireMatchRequest(self):
		if self.amount >= settings.fireMatchCost:
			self.amount -= settings.fireMatchCost
			controller = mvcState.GetController()
			controller.GameEvent( 'BoughtFireMatch' )

	def OnWaterWheelRepairRequest(self):
		if self.amount >= settings.waterWheelRepairCost:
			self.amount -= settings.waterWheelRepairCost
			controller = mvcState.GetController()
			controller.GameEvent( 'BoughtWaterWheelRepair' )

	def OnNukeFuelRequest(self):
		if self.amount >= settings.nukeFuelCost:
			self.amount -= settings.nukeFuelCost
			controller = mvcState.GetController()
			controller.GameEvent( 'BoughtNukeFuel' )

#-----------------------------------------------------------------------------
class Heater:
	def __init__(self):
		self.temperature = 20
		self.timeSinceBubbleLaunch = 0
	def BubbleLaunch( self ):
		self.timeSinceBubbleLaunch = 0
		controller = mvcState.GetController()
		controller.GameEvent('BubbleLaunch', self.rect.centerx )
	def update( self, timeChange ): 
		self.timeSinceBubbleLaunch += timeChange
		if self.temperature > 500 \
		  and self.timeSinceBubbleLaunch >  bubbleRate500Degrees:
			self.BubbleLaunch()
			self.BubbleLaunch()
			self.BubbleLaunch()
		elif self.temperature > 190 \
		  and self.timeSinceBubbleLaunch >  bubbleRate190Degrees:
			self.BubbleLaunch()
		elif self.temperature > 100 \
		  and self.timeSinceBubbleLaunch > bubbleRate100Degrees:
			self.BubbleLaunch()
		elif self.temperature > 80 \
		  and self.timeSinceBubbleLaunch >  bubbleRate80Degrees:
			self.BubbleLaunch()


#-----------------------------------------------------------------------------
class ManualHeater(Sprite, Heater):
	def __init__(self):
		Sprite.__init__(self)
		Heater.__init__(self)

		self.hiTempLimit = 200
		self.lowTempLimit = 10
		self.isHeating = 0

		self.cursorIndex = 0
		self.xlens = precomputed_circle.xlens[:]
		self.ylens = precomputed_circle.ylens[:]

		self.redImg= load_png( 'manual_heater_on.png' )
		self.blackImg = load_png( 'manual_heater_off.png' )
		self.cursorImg = load_png( 'heater_cursor.png' )
		self.cursorRect = self.cursorImg.get_rect()
		self.rect = self.blackImg.get_rect()
		self.ComposeImg()


		self.dirty = 1

	def ComposeImg( self ): 
		self.image = self.blackImg.convert_alpha()
		tRange = self.hiTempLimit - self.lowTempLimit
		tempPercent = float(self.temperature-self.lowTempLimit)/tRange
		redImg = self.redImg.convert_alpha()
		change_alpha_mult( redImg, int(tempPercent*100) )
		redImg.unlock()

		self.image.blit( redImg, (0,0) )

		x = self.xlens[self.cursorIndex]
		y = self.ylens[self.cursorIndex]
		self.cursorRect.center = ( self.rect.width/2 + x,
		                           self.rect.height/2 + y )
		self.image.blit( self.cursorImg, self.cursorRect.topleft )


	def update( self, timeChange ): 
		Heater.update( self, timeChange )
		self.timeSinceBubbleLaunch += timeChange

		if self.dirty:
			self.ComposeImg()

		if not self.isHeating and self.temperature > self.lowTempLimit:
			self.temperature -= 1

		self.isHeating = 0



	def BubbleLaunch( self ):
		self.timeSinceBubbleLaunch = 0
		controller = mvcState.GetController()
		controller.GameEvent('BubbleLaunch', self.rect.centerx )

	def MouseInCursor( self ):
		self.cursorIndex += 1
		self.cursorIndex %= len( self.xlens )
		self.isHeating = 1
		self.dirty = 1
		self.temperature += 5
		if self.temperature > self.hiTempLimit:
			self.temperature = self.hiTempLimit
		#log.debug( self.temperature )

	def OnMouseMove( self, event ): 
		translatedPos = (event.pos[0] - self.rect.x,
		                event.pos[1] - self.rect.y)
		if self.cursorRect.collidepoint( translatedPos ):
			self.MouseInCursor()


	def OnMouseDown( self, pos ): 
		pass
	def OnMouseUp( self, pos ): 
		pass

#-----------------------------------------------------------------------------
class BuyableHeater:
	def OnMouseMove( self, event ): 
		if self.isActive:
			return

		pos = event.pos
		if self.image == self.offImg and self.rect.collidepoint( pos ):
			self.hasMouseFocus = True
		elif self.image == self.focusImg \
		  and not self.rect.collidepoint( pos ):
			self.hasMouseFocus = False

	def OnMouseDown( self, pos ): 
		if self.rect.collidepoint( pos ):
			self.isClicking = True
	def OnMouseUp( self, pos ): 
		if self.rect.collidepoint( pos ) and self.isClicking:
			self.Click()
	def Click( self, eventToFire ): 
		self.image = self.onImg
		self.isActive = True
		controller = mvcState.GetController()
		controller.GameEvent( eventToFire )

#-----------------------------------------------------------------------------
class SolarHeater(Sprite, Heater, BuyableHeater):
	def __init__(self):
		Sprite.__init__(self)
		Heater.__init__(self)

		self.temperature = 81
		self.isActive = False
		self.hasMouseFocus = False
		self.isClicking = False

		self.offImg   = load_png( 'solar_off.png' )
		self.onImg    = load_png( 'solar_on.png' )
		self.focusImg = load_png( 'solar_focus.png' )
		self.image = self.offImg
		self.rect = self.image.get_rect()

		controller = mvcState.GetController()
		controller.mouseListeners.append( self )
		controller.GameEvent( 'HeaterBirth', self )

	def update( self, timeChange ): 
		if self.isActive:
			Heater.update( self, timeChange )
		elif self.hasMouseFocus:
			self.image = self.focusImg
		elif not self.hasMouseFocus:
			self.image = self.offImg

	def Click( self ): 
		if not self.isActive:
			BuyableHeater.Click( self, 'BoughtSolar' )

#----------------------------------------------------------------------------
class WindHeater(Sprite, Heater, BuyableHeater):
	def __init__(self):
		Sprite.__init__(self)
		Heater.__init__(self)

		self.temperature = 0
		self.isActive = False
		self.hasMouseFocus = False
		self.isClicking = False

		self.isSpinning = False
		self.timeSinceStartSpinning = 0
		self.timeSinceStopSpinning = 0
		self.timeUntilNextGust = rng.randint( settings.windGustTimeMin,
		                                      settings.windGustTimeMax )
		self.spinDuration = 0
		self.lastAnimFrameTime = 0
		self.lastAnimFrameIndex = 0

		self.offImg   = load_png( 'wind_off.png' )
		self.onImg    = load_png( 'wind00.png' )
		self.focusImg = load_png( 'wind_focus.png' )
		self.image = self.offImg
		self.rect = self.image.get_rect()

		self.spiningImgs = [
		                    load_png( 'wind00.png' ),
		                    load_png( 'wind01.png' ),
		                    load_png( 'wind02.png' ),
		                   ]

		controller = mvcState.GetController()
		controller.mouseListeners.append( self )
		controller.GameEvent( 'HeaterBirth', self )

	def update( self, timeChange ): 
		if not self.isActive:
			if self.hasMouseFocus:
				self.image = self.focusImg
			elif not self.hasMouseFocus:
				self.image = self.offImg
			return

		Heater.update( self, timeChange )

		if self.isSpinning:
			self.AnimateSpin( timeChange )
			self.timeSinceStartSpinning += timeChange
			if self.timeSinceStartSpinning > self.spinDuration:
				self.StopSpin()
		else:
			self.timeSinceStopSpinning += timeChange
			if self.timeSinceStopSpinning > self.timeUntilNextGust:
				self.StartSpin()

	def StartSpin( self ): 
		#log.debug( 'starting spin' )
		self.timeSinceStartSpinning = 0
		self.isSpinning = True
		self.temperature = settings.windTemperature
		self.spinDuration = rng.randint( settings.windSpinningMin,
		                                 settings.windSpinningMax )
	def StopSpin( self ): 
		#log.debug( 'stopping spin' )
		self.timeSinceStopSpinning = 0
		self.isSpinning = True
		self.isSpinning = False
		self.temperature = 0
		self.timeUntilNextGust = rng.randint( settings.windGustTimeMin,
		                                      settings.windGustTimeMax )

	def AnimateSpin( self, timeChange ): 
		self.lastAnimFrameTime += timeChange
		if self.lastAnimFrameTime < 200:
			return
		self.lastAnimFrameTime = 0
		self.lastAnimFrameIndex += 1
		self.lastAnimFrameIndex %= len(self.spiningImgs)
		self.image = self.spiningImgs[self.lastAnimFrameIndex]


	def Click( self ): 
		if not self.isActive:
			BuyableHeater.Click( self, 'BoughtWind' )

#-----------------------------------------------------------------------------
class FireHeater(Sprite, Heater, BuyableHeater):
	def __init__(self):
		Sprite.__init__(self)
		Heater.__init__(self)

		self.temperature = 300
		self.hiTempLimit = 300
		self.lowTempLimit = 20
		self.isActive = False
		self.hasMouseFocus = False
		self.isClicking = False

		self.offImg   = load_png( 'fire_off.png' )
		self.onImg    = load_png( 'fire_on.png' )
		self.focusImg = load_png( 'fire_focus.png' )
		self.outImg   = load_png( 'fire_out.png' )
		self.matchImg = load_png( 'fire_match_off.png' )
		self.matchFocusImg = load_png( 'fire_match_focus.png' )
		self.image = self.offImg
		self.rect = self.image.get_rect()

		self.cursorComposer = CursorComposer( [5,70], [70,70] )
		self.cursorComposer.BeginLoopCallback = self.BeginCursorLoop
		self.cursorComposer.EndLoopCallback = self.EndCursorLoop

		self.isExtinguished = False
		self.isBuyingMatch = False
		self.timeSinceStarted = 0
		self.strikeTimeCounter = 0
		self.fullStrikeTime = 0
		self.fireStrikeLimit = settings.fireStrikeLimit

		controller = mvcState.GetController()
		controller.mouseListeners.append( self )
		controller.gameEventListeners.append( self )
		controller.GameEvent( 'HeaterBirth', self )

	def update( self, timeChange ): 
		if not self.isActive:
			if self.hasMouseFocus:
				self.image = self.focusImg
			elif not self.hasMouseFocus:
				self.image = self.offImg
			return

		self.cursorComposer.BeginUpdate()

		Heater.update( self, timeChange )

		if self.timeSinceStarted == 0:
			self.image = self.onImg

		self.timeSinceStarted += timeChange

		if self.isBuyingMatch:
			#log.debug( 'is buying match.  set image' )
			if self.image == self.matchImg \
			  and self.hasMouseFocus:
				self.image = self.matchFocusImg
			elif self.image == self.matchFocusImg \
			  and not self.hasMouseFocus:
				self.image = self.matchImg
		elif self.isExtinguished:
			self.ComposeImg()
			if self.isStriking:
				self.strikeTimeCounter += timeChange
			elif self.fullStrikeTime > 0:
				if self.fullStrikeTime < self.fireStrikeLimit:
					self.Kindle()
				else:
					self.StrikeFail()
		else:
			if self.timeSinceStarted > settings.fireDuration:
				self.Extinguish()


	def Kindle( self ): 
		self.isExtinguished = False
		self.temperature = 300
		self.timeSinceStarted = 0
		self.fullStrikeTime = 0

		controller = mvcState.GetController()
		controller.GameEvent( 'FireKindle' )

	def StrikeFail( self ): 
		self.fullStrikeTime = 0
		controller = mvcState.GetController()
		controller.GameEvent( 'FireStrikeFail' )

	def Extinguish( self ): 
		self.isExtinguished = True
		self.isBuyingMatch = True
		self.hasMouseFocus = False
		self.temperature = 20
		self.isStriking = False
		self.fullStrikeTime = 0

		self.image = self.matchImg

	def BeginCursorLoop(self):
		self.isStriking = True
		self.strikeTimeCounter = 0

	def EndCursorLoop( self ):
		self.isStriking = False
		self.fullStrikeTime = self.strikeTimeCounter
		log.debug( 'match strike took ms: '+ str( self.fullStrikeTime ))

	def OnMouseMove( self, event ): 
		BuyableHeater.OnMouseMove(self, event)

		pos = event.pos
		if self.isBuyingMatch:
			if self.rect.collidepoint( pos ):
				self.hasMouseFocus = True
			else:
				self.hasMouseFocus = False

		elif self.isExtinguished:
			translatedPos = (pos[0] - self.rect.x,
			                 pos[1] - self.rect.y)
			self.cursorComposer.OnMouseMove( translatedPos )

	def ComposeImg( self ): 
		self.image = self.cursorComposer.Update( self.outImg )

	def Click( self ): 
		if not self.isActive:
			BuyableHeater.Click( self, 'BoughtFire' )
		if self.isBuyingMatch:
			controller = mvcState.GetController()
			controller.GameEvent( 'FireMatchRequest' )

	def OnBoughtFireMatch( self ): 
		self.isBuyingMatch = False

#----------------------------------------------------------------------------
class WaterWheelHeater(Sprite, Heater, BuyableHeater):
	def __init__(self):
		Sprite.__init__(self)
		Heater.__init__(self)

		self.temperature = settings.waterWheelTemperature
		self.isActive = False
		self.hasMouseFocus = False
		self.isClicking = False

		self.isBuyingRepair = False
		self.isBroken = False
		self.isAccelerated = False
		self.timeSinceStarted = 0
		self.lastAnimFrameTime = 0
		self.lastAnimFrameIndex = 0
		self.timeSinceAccelerated = 0

		self.offImg   = load_png( 'waterwheel_off.png' )
		self.focusImg = load_png( 'waterwheel_focus.png' )
		self.repairImg = load_png( 'waterwheel_repair.png' )
		self.repairFocusImg = load_png( 'waterwheel_repair_focus.png' )
		self.images = [ load_png( 'waterwheel00.png' ),
		                load_png( 'waterwheel01.png' ),
		                load_png( 'waterwheel02.png' ),
		              ]
		self.onImg   = self.images[0]
		self.image = self.offImg
		self.rect = self.image.get_rect()

		self.cursorComposer = CursorComposer( [25,68,35], [15,50,68] )
		self.cursorComposer.EndLoopCallback = self.BeginAcceleration


		controller = mvcState.GetController()
		controller.mouseListeners.append( self )
		controller.gameEventListeners.append( self )
		controller.GameEvent( 'HeaterBirth', self )

	def update( self, timeChange ): 
		if not self.isActive:
			if self.hasMouseFocus:
				self.image = self.focusImg
			elif not self.hasMouseFocus:
				self.image = self.offImg
			return

		self.cursorComposer.BeginUpdate()

		Heater.update( self, timeChange )

		if self.timeSinceStarted == 0:
			self.image = self.images[0]

		self.timeSinceStarted += timeChange


		if self.isBuyingRepair:
			#log.debug( 'is buying repair.  set image' )
			if self.image == self.repairImg \
			  and self.hasMouseFocus:
				self.image = self.repairFocusImg
			elif self.image == self.repairFocusImg \
			  and not self.hasMouseFocus:
				self.image = self.repairImg

		elif not self.isAccelerated:
			self.ComposeImg()
			self.AnimateSpin( timeChange )
			if self.timeSinceStarted > settings.waterWheelDuration:
				self.Brake()

		else: #accelerated mode
			self.timeSinceAccelerated += timeChange
			if self.timeSinceAccelerated > \
			   settings.waterWheelAccelerationDuration:
				self.StopAcceleration()
			self.AnimateSpin( timeChange )

	def ComposeImg( self ): 
		i = self.lastAnimFrameIndex
		self.image = self.cursorComposer.Update( self.images[i] )

	def AnimateSpin( self, timeChange ): 
		self.lastAnimFrameTime += timeChange

		animTimeout = 300

		if self.isAccelerated:
			animTimeout = 100

		if self.lastAnimFrameTime < animTimeout:
			return
		self.lastAnimFrameTime = 0
		self.lastAnimFrameIndex += 1
		self.lastAnimFrameIndex %= len(self.images)
		self.image = self.images[self.lastAnimFrameIndex]

	def BeginAcceleration( self ): 
		self.isAccelerated = True
		self.timeSinceAccelerated = 0
		self.temperature = settings.waterWheelAcceleratedTemperature

		controller = mvcState.GetController()
		controller.GameEvent( 'WaterWheelAccelerated' )

	def StopAcceleration( self ): 
		self.isAccelerated = False
		self.temperature = settings.waterWheelTemperature

	def Brake( self ): 
		#log.debug( 'water wheel BRAKE' )
		self.hasMouseFocus = False
		self.isBuyingRepair = True
		self.temperature = 0
		self.image = self.repairImg

	def OnBoughtWaterWheelRepair( self ): 
		self.timeSinceStarted = 0
		self.isBuyingRepair = False
		self.temperature = settings.waterWheelTemperature

		controller = mvcState.GetController()
		controller.GameEvent( 'WaterWheelRepaired' )

	def Click( self ): 
		if not self.isActive:
			BuyableHeater.Click( self, 'BoughtWaterWheel' )
		if self.isBuyingRepair:
			controller = mvcState.GetController()
			controller.GameEvent( 'WaterWheelRepairRequest' )

	def OnMouseMove( self, event ): 
		BuyableHeater.OnMouseMove(self, event)

		pos = event.pos
		if self.isBuyingRepair:
			if self.rect.collidepoint( pos ):
				self.hasMouseFocus = True
			else:
				self.hasMouseFocus = False
		elif not self.isAccelerated:
			translatedPos = (pos[0] - self.rect.x,
			                 pos[1] - self.rect.y)
			self.cursorComposer.OnMouseMove( translatedPos )



#----------------------------------------------------------------------------
class NuclearHeater(Sprite, Heater, BuyableHeater):
	def __init__(self):
		Sprite.__init__(self)
		Heater.__init__(self)

		self.temperature = 0
		self.isActive = False
		self.hasMouseFocus = False
		self.isClicking = False

		self.isBuyingFuel = True
		self.amountUsedFuel = 0
		self.usedFuelCapacity = 5
		self.timeSinceStarted = 0

		self.offImg   = load_png( 'nuke_off.png' )
		self.onImgs   = [
		                 load_png( 'nuke_on01.png' ),
		                 load_png( 'nuke_on02.png' ),
		                 load_png( 'nuke_on03.png' ),
		                 load_png( 'nuke_on04.png' ),
		                 load_png( 'nuke_on05.png' ),
		                ]
		self.onImg    = load_png( 'nuke_on.png' )
		self.focusImg = load_png( 'nuke_focus.png' )
		self.fullImg  = load_png( 'nuke_full.png' )
		self.fuelImgs = [
		                 load_png( 'nuke_fuel01.png' ),
		                 load_png( 'nuke_fuel02.png' ),
		                 load_png( 'nuke_fuel03.png' ),
		                 load_png( 'nuke_fuel04.png' ),
		                 load_png( 'nuke_fuel05.png' ),
		                ]
		self.fuelImg  = load_png( 'nuke_fuel.png' )
		self.fuelFocusImgs = [
		                 load_png( 'nuke_fuel_focus01.png' ),
		                 load_png( 'nuke_fuel_focus02.png' ),
		                 load_png( 'nuke_fuel_focus03.png' ),
		                 load_png( 'nuke_fuel_focus04.png' ),
		                 load_png( 'nuke_fuel_focus05.png' ),
		                ]
		self.fuelFocusImg = load_png( 'nuke_fuel_focus.png' )
		self.image = self.offImg
		self.rect = self.image.get_rect()

		controller = mvcState.GetController()
		controller.mouseListeners.append( self )
		controller.gameEventListeners.append( self )
		controller.GameEvent( 'HeaterBirth', self )

	def update( self, timeChange ): 
		if not self.isActive:
			if self.hasMouseFocus:
				self.image = self.focusImg
			elif not self.hasMouseFocus:
				self.image = self.offImg
			return

		if self.amountUsedFuel >= self.usedFuelCapacity:
			self.image = self.fullImg
			return

		if self.timeSinceStarted == 0:
			if self.amountUsedFuel == 0:
				self.image = self.onImg
			else:
				self.image = self.onImgs[self.amountUsedFuel-1]

		self.timeSinceStarted += timeChange

		if self.isBuyingFuel:
			#log.debug( 'is buying Fuel.  set image' )
			if self.hasMouseFocus:
				if self.amountUsedFuel == 0:
					self.image = self.fuelFocusImg
				else:
					self.image = self.fuelFocusImgs[
					                  self.amountUsedFuel-1]
			else:
				if self.amountUsedFuel == 0:
					self.image = self.fuelImg
				else:
					self.image = self.fuelImgs[
					                  self.amountUsedFuel-1]
		else:
			Heater.update( self, timeChange )
			if self.timeSinceStarted > settings.nukeDuration:
				self.ExhaustFuel()


	def ExhaustFuel( self ): 
		#log.debug( 'nuke fuel exhausted' )
		self.amountUsedFuel += 1
		self.hasMouseFocus = False
		self.isBuyingFuel = True
		self.temperature = 0
		self.image = self.fuelImgs[self.amountUsedFuel-1]

	def OnBoughtNukeFuel( self ): 
		self.timeSinceStarted = 0
		self.isBuyingFuel = False
		self.temperature = settings.nukeTemperature

		controller = mvcState.GetController()
		controller.GameEvent( 'NukeFueled' )

	def Click( self ): 
		if not self.isActive:
			BuyableHeater.Click( self, 'BoughtNuke' )
			return

		if self.isBuyingFuel:
			controller = mvcState.GetController()
			controller.GameEvent( 'NukeFuelRequest' )

	def OnMouseMove( self, event ): 
		BuyableHeater.OnMouseMove(self, event)

		pos = event.pos
		if self.isBuyingFuel:
			if self.rect.collidepoint( pos ):
				self.hasMouseFocus = True
			else:
				self.hasMouseFocus = False

#----------------------------------------------------------------------------
class SqueezePrompt(Sprite):
	def __init__(self, bladder):
		Sprite.__init__(self)

		self.bladder = bladder
		self.topBottomSpacing = 40
		self.composeTimeout = 100

		self.squeezeImgs = [
		                    load_png( 'squeeze_violet.png' ),
		                    load_png( 'squeeze_blue.png' ),
		                    load_png( 'squeeze_green.png' ),
		                    load_png( 'squeeze_yellow.png' ),
		                    load_png( 'squeeze_orange.png' ),
		                    load_png( 'squeeze_red.png' ),
		                   ]
		self.arrowTop =  load_png( 'squeeze_arrow_top.png' )
		self.arrowBot =  load_png( 'squeeze_arrow_bot.png' )
		self.image = self.squeezeImgs[0]
		self.rect = self.image.get_rect()
		self.arrowTopRect = self.arrowTop.get_rect()
		self.arrowBotRect = self.arrowBot.get_rect()
		self.ComposeImg()


		controller = mvcState.GetController()
		controller.mouseListeners.append( self )

	def kill( self ):
		Sprite.kill( self )
		controller = mvcState.GetController()
		controller.mouseListeners.remove( self )

	def ComposeImg( self ): 
		#TODO: UGH!  can you say nasty coupling?
		index = self.bladder.squeezeFactor
		self.image = pygame.Surface( self.rect.size, SRCALPHA, 32 )
		
		topHeight = self.arrowTopRect.height
		y = self.rect.height/2 - (self.topBottomSpacing/2 + topHeight)
		self.image.blit( self.arrowTop, (34,y) )

		y = self.rect.height/2 + (self.topBottomSpacing/2)
		self.image.blit( self.arrowBot, (34,y) )

		self.image.blit( self.squeezeImgs[index], (0,0) )
		
	def update( self, timeChange ): 
		self.composeTimeout -= timeChange
		if self.composeTimeout < 0:
			self.composeTimeout = 100
			self.ComposeImg()

	def OnMouseMove( self, event ): 
		if not self.bladder.isShooting:
			return
		rect = self.bladder.rect
		distFromCenter = min( abs(event.pos[0]-rect.centerx), 199 )
		percentage = float(distFromCenter)/199
		self.topBottomSpacing = 40 - int( percentage*40 )
			
	def OnMouseDown( self, pos ): 
		pass

	def OnMouseUp( self, pos ): 
		pass
	

#----------------------------------------------------------------------------
class QuitButton(Sprite):
	def __init__(self):
		Sprite.__init__(self)

		self.onImg = load_png( 'quit_btn.png' )
		self.focusImg = load_png( 'quit_btn_focus.png' )
		self.image = self.onImg
		self.rect = self.image.get_rect()

		self.isClicking = False
		self.hasMouseFocus = False

		controller = mvcState.GetController()
		controller.mouseListeners.append( self )

	def kill( self ):
		Sprite.kill(self)
		controller = mvcState.GetController()
		controller.mouseListeners.remove( self )
		
	def update( self, timeChange ): 
		if self.hasMouseFocus:
			self.image = self.focusImg
		else:
			self.image = self.onImg

	def OnMouseMove( self, event ): 
		pos = event.pos
		if self.image == self.onImg and self.rect.collidepoint( pos ):
			self.hasMouseFocus = True
		elif self.image == self.focusImg \
		  and not self.rect.collidepoint( pos ):
			self.hasMouseFocus = False

	def OnMouseDown( self, pos ): 
		if self.rect.collidepoint( pos ):
			self.isClicking = True
	def OnMouseUp( self, pos ): 
		if self.rect.collidepoint( pos ) and self.isClicking:
			self.Click()
	def Click( self ): 
		self.image = self.onImg
		controller = mvcState.GetController()
		controller.GameEvent( "UserQuit" )

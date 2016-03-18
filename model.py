import mvcState
from pygame.sprite import RenderUpdates
from sets import Set
from pygame import Rect
from log import log
from objects import Bladder, ManualHeater, Bubble, Cloud, Stripe, Geyser, Drop,Purse, SolarHeater, WaterWheelHeater, WindHeater, FireHeater, NuclearHeater, MoneyWidget, Lock, InstructionSpin, InstructionPress, SqueezePrompt, QuitButton

import settings
from utils import COLORS
try:
    from poutine.statusbar import StatusBar
except ImportError:
    pass # OMG THIS WILL FAIL
from random import Random
rng = Random()

class View:
	def ModelStarted( self, model ):
		self.model = model
		self.screen.blit( self.bgImage, (0,0) )
		self.display.flip()

	def Clear( self ):
		for group in self.groups:
			group.clear( self.screen, self.bgImage )

	def Draw( self ):
		changedRects = []
		for group in self.groups:
			changedRects += group.draw(self.screen)
		self.display.update( changedRects )

	def Update( self, timeChange ):
		pass

class GameView(View):
	def __init__( self, screen, display ):
		self.screen = screen
		self.screenRect = screen.get_rect()
		self.display = display
		self.model = None
		self.currentTime = 0

		self.bgImage = load_png( 'bg_game.png' )

		self.hiGroup = RenderUpdates()
		self.lowGroup = RenderUpdates()
		self.viewOnlyGroup = RenderUpdates()
		self.bubbleGroup = RenderUpdates()

		self.ins_spin = None
		self.ins_press = None
		self.quitButton = None
		self.squeezePrompt = None

		self.groups = [self.lowGroup, self.bubbleGroup, self.hiGroup, self.viewOnlyGroup]
		self.locks = []

		self.stripeOrder = ['violet','blue','green',
		                    'yellow','orange','red']
		self.stripeHeights = {
		                     'violet': 233,
		                     'blue':   189, 
		                     'green':  136,
		                     'yellow': 85,
		                     'orange': 44,
		                     'red':    11,
		                    }
		self.heaterRects = { 
		                    'green':  Rect ( 160, 470, 80, 100 ),
		                    'blue':   Rect ( 265, 470, 80, 100 ),
		                    'violet': Rect ( 370, 470, 80, 100 ),
		                    'red':    Rect ( 475, 470, 80, 100 ),
		                    'orange': Rect ( 580, 470, 80, 100 ),
		                    'yellow': Rect ( 685, 470, 80, 100 ),
		}


		self.purseStatusbars = []

		controller = mvcState.GetController()
		controller.gameEventListeners.append( self )

	def ModelStarted( self, model ):
		self.quitButton = QuitButton()
		self.quitButton.rect.topleft = (10, 530)
		self.viewOnlyGroup.add( self.quitButton )

		self.ins_spin = InstructionSpin()
		self.ins_spin.rect.topleft = (380, 440)
		self.viewOnlyGroup.add( self.ins_spin )

		View.ModelStarted( self, model )
		heater = self.model.manualHeater
		heater.rect.topleft = self.heaterRects['red'].topleft
		self.hiGroup.add( heater )

		cloud = self.model.cloud
		cloud.rect.topleft = (10,40)
		self.hiGroup.add( cloud )
		
		monWid = self.model.playerMoney
		monWid.rect.topleft = (10,490)
		self.hiGroup.add( monWid )

		bladder = self.model.bladder
		bladder.rect.topleft = (410,378)
		bladder.FixBottom( bladder.rect.midbottom )
		self.hiGroup.add( bladder )

		self.squeezePrompt = SqueezePrompt( bladder )
		self.squeezePrompt.rect.topleft = (190,340)

		m = self.model
		stripes = [m.violetstripe, m.bluestripe, m.greenstripe,
		           m.yellowstripe, m.orangestripe, m.redstripe ]
		for i in range( len(stripes) ):
			name = stripes[i].name
			stripes[i].rect.topleft = (146,self.stripeHeights[name])
			self.lowGroup.add( stripes[i] )

		for i in range( len(m.colorPurses) ):
			cName = m.colorPurses[i].colorName
			dimensions = self.heaterRects[cName].move(0,0)
			dimensions.move_ip(0,100)
			dimensions.height = 10
			sb = StatusBar( m.colorPurses[i], 
			         dimensions,
			         outlineImg='sb_outline.png',
			         attrName='amount', 
			         fullAmt=m.colorPurses[i].capacity,
			         innerColor=COLORS[cName]
			        )
			self.purseStatusbars.append( sb )
			self.lowGroup.add( sb )


	def OnBubbleLaunch( self, centerx ):
		#log.debug( 'bubble birth' )
		if self.ins_spin:
			self.ins_spin.kill()
			self.ins_spin = None

		bubble = Bubble( 438 )
		minX = 140
		maxX = 790
		xpos = int(rng.normalvariate( 0,50 )) + centerx
		xpos = min( xpos, maxX )
		xpos = max( xpos, minX )
		bubble.rect.x = xpos
		bubble.rect.bottom = 470
		self.bubbleGroup.add( bubble )

	def Update( self, timeChange ):
		self.viewOnlyGroup.update( timeChange )
		self.bubbleGroup.update( timeChange )

		self.currentTime += timeChange
		#twoSecondsAgo = self.currentTime - 2000
		#halfSecondAgo = self.currentTime - 500

		heaterRange = [444,530]

		for sb in self.purseStatusbars:
			sb.update()

	def OnBladderShoot( self, power, height ):
		if self.ins_press:
			self.ins_press.kill()
		if height > 3:
			gey = Geyser( "tall" )
		else:
			gey = Geyser( "short" )
		colorName = self.stripeOrder[height]
		gey.rect.midtop = (450, self.stripeHeights[colorName])
		self.viewOnlyGroup.add( gey )

		self.viewOnlyGroup.add( self.squeezePrompt )
		#print len(self.viewOnlyGroup)

	def OnBladderShootStop( self ):
		self.viewOnlyGroup.remove( self.squeezePrompt )

	def OnBladderVent( self, power, height ):
		if height > 3:
			gey = Geyser( "tall" )
		else:
			gey = Geyser( "short" )
		colorName = self.stripeOrder[height]
		gey.rect.midtop = (450, self.stripeHeights[colorName])
		self.viewOnlyGroup.add( gey )

	def OnDropBirth( self, drop ):
		self.lowGroup.add( drop )

	def OnStripeHitMaxOpacity(self, stripe):
		yPos = self.stripeHeights[stripe.name]+4
		if yPos in [lock.rect.top for lock in self.locks]:
			#log.debug( 'already have that lock' )
			return
		lock = Lock()
		lock.rect.topleft = (111, self.stripeHeights[stripe.name]+4 )
		self.hiGroup.add( lock )
		self.locks.append( lock )

	def OnHeaterBirth( self, heater ):
		switch= { SolarHeater:'violet',
		          WaterWheelHeater:'blue',
		          WindHeater:'green',
		          FireHeater:'yellow',
		          NuclearHeater:'orange',
		}
		klass = heater.__class__
		heater.rect.topleft = self.heaterRects[switch[klass]].topleft
		self.hiGroup.add( heater )

	def OnBladderVentingImminent( self ):
		if self.ins_press == None:
			self.ins_press = InstructionPress()
			self.ins_press.rect.topleft = (560, 300)
			self.viewOnlyGroup.add( self.ins_press )

	def Kill( self ):
		controller = mvcState.GetController()
		controller.gameEventListeners.remove( self )
		for s in self.viewOnlyGroup.sprites():
			s.kill()
		for s in self.bubbleGroup.sprites():
			s.kill()

	def OnUserQuit( self ):
		self.Kill()

	def OnWin( self, time, money ):
		self.Kill()

class FreestyleModel:
	def __init__( self ):
		self.time = 0

		try:
			self._ImportSettings()
		except Exception, e:
			log.debug( "GOT EXCEPTION CHANGING SETTINGS" )
			log.debug( e )
				

		self.colorPurses = [
		                    Purse('violet'),
		                    Purse('blue'),
		                    Purse('green'),
		                    Purse('yellow'),
		                    Purse('orange'),
		                    Purse('red'),
		                   ]

		self.finishedStripes = Set()

		self.objects = RenderUpdates()

		self.playerMoney = MoneyWidget( 0, True )
		self.objects.add( self.playerMoney )

		self.manualHeater = ManualHeater()
		self.objects.add( self.manualHeater )

		self.cloud = Cloud()
		self.objects.add( self.cloud )

		self.bladder = Bladder()
		self.objects.add( self.bladder )

		self.violetstripe = Stripe( 'violet', 0 )
		self.objects.add( self.violetstripe )
		self.bluestripe = Stripe( 'blue', 1 )
		self.objects.add( self.bluestripe )
		self.greenstripe = Stripe( 'green', 2 )
		self.objects.add( self.greenstripe )
		self.yellowstripe = Stripe( 'yellow', 3 )
		self.objects.add( self.yellowstripe )
		self.orangestripe = Stripe( 'orange', 4 )
		self.objects.add( self.orangestripe )
		self.redstripe = Stripe( 'red', 5 )
		self.objects.add( self.redstripe )

		self.bonusStripesThisRound = []

	def _ImportSettings(self):
		import settings_freestyle as s_f
		for attrName in dir(s_f):
			setattr( settings, attrName, getattr(s_f,attrName) )

	def Update( self, timeChange ):
		self.bonusStripesThisRound = []

		self.time += timeChange
		self.objects.update( timeChange )

		if self.bonusStripesThisRound and not self.cloud.isDripping:
			stripe = rng.choice( self.bonusStripesThisRound )
			colorName = stripe.name
			self.cloud.StartDrip( colorName )

	def Start( self ):
		mvcState.GetView().ModelStarted(self)

		controller = mvcState.GetController()
		controller.mouseListeners.append( self.manualHeater )
		controller.gameEventListeners.append( self )

	def Quit( self ):
		controller = mvcState.GetController()
		controller.gameEventListeners.remove( self )

		for s in self.objects.sprites():
			s.kill()

		#log.debug( "SETTING MM FLAG" )
		mvcState.SetModel( MainMenuFlag() )

	def OnUserQuit( self ):
		#log.debug( "FMODEL GOT UQUIT" )
		self.Quit()

	def OnWin( self, time, money ):
		#log.debug( "FMODEL GOT WIIIIIIIIIIIIIIIIIIIIIN" )
		controller = mvcState.GetController()
		controller.gameEventListeners.remove( self )

		for s in self.objects.sprites():
			s.kill()

		mvcState.SetModel( WinScreenModel( time, money ) )

	def OnStripeAtBonusOpacity( self, stripe ):
		self.bonusStripesThisRound.append( stripe )

	def OnLaunchDrop( self, pos, colorName ):
		drop = Drop( colorName, pos )
		self.objects.add( drop )

	def OnDropOverCapacity( self, colorName ):
		log.debug( 'adding 10 money' )
		self.playerMoney.ChangeMoney( 10 )

	def OnPurseFull( self, colorName ):
		switch= { 'violet': SolarHeater,
		          'blue': WaterWheelHeater,
		          'green': WindHeater,
		          'yellow': FireHeater,
		          'orange': NuclearHeater,
		          'red': None
		}
		klass = switch[colorName]
		if not klass:
			return
		for s in self.objects.sprites():
			if s.__class__ == klass:
				return
		newHeater = klass()
		self.objects.add( newHeater )

	def OnStripeHitMaxOpacity(self, stripe):
		self.finishedStripes.add( stripe )
		#print self.finishedStripes
		#print [s.name for s in self.finishedStripes]
		if len(self.finishedStripes) == 6:
			controller = mvcState.GetController()
			log.debug( "WIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIN" )
			log.debug( str((self.time, self.playerMoney.amount ) ) )
			controller.GameEvent( "Win", self.time, 
			                      self.playerMoney.amount )


#NOTE: the MainMenu is also a View
from utils import load_png
from gui import ImgButton
class MainMenu(View):
	def __init__( self, screen, display ):
		self.nextModelClass = None
		self.screen = screen
		self.screenRect = screen.get_rect()
		self.display = display

		self.model = None

		self.bgImage = load_png( 'bg_mainmenu.png' )

		self.btnGroup = RenderUpdates()

		fBtn = ImgButton( 'freestyle', self.Freestyle )
		fBtn.rect.midtop = self.screenRect.midtop
		fBtn.rect.y += 100
		self.btnGroup.add( fBtn )
		self.freestyleButton = fBtn

		fBtn = ImgButton( 'freestyle_tricky', self.FreestyleTricky )
		fBtn.rect.midtop = self.screenRect.midtop
		fBtn.rect.y += 160
		self.btnGroup.add( fBtn )
		self.freestyleTrickyButton = fBtn

		fBtn = ImgButton( 'speedy', self.Speedy )
		fBtn.rect.midtop = self.screenRect.midtop
		fBtn.rect.y += 220
		self.btnGroup.add( fBtn )
		self.speedyButton = fBtn

		fBtn = ImgButton( 'sharpshooter', self.Sharpshooter )
		fBtn.rect.midtop = self.screenRect.midtop
		fBtn.rect.y += 280
		self.btnGroup.add( fBtn )
		self.sharpshooterButton = fBtn

		fBtn = ImgButton( 'firehose', self.Firehose )
		fBtn.rect.midtop = self.screenRect.midtop
		fBtn.rect.y += 340
		self.btnGroup.add( fBtn )
		self.firehoseButton = fBtn

		fBtn = ImgButton( 'loading', self.Loading )
		fBtn.rect.midtop = self.screenRect.midtop
		fBtn.rect.y += 400
		self.loadingButton = fBtn


		dBtn = ImgButton( 'debug', self.Debug )
		dBtn.rect.midbottom = self.screenRect.midbottom
		dBtn.rect.y -= 10
		self.btnGroup.add( dBtn )
		self.debugButton = dBtn

		self.groups = [ self.btnGroup ]


	def Update( self, timeChange ):
		self.btnGroup.update()

	def Start( self ):
		controller = mvcState.GetController()
		controller.mouseListeners.append( self.freestyleButton )
		controller.mouseListeners.append( self.freestyleTrickyButton )
		controller.mouseListeners.append( self.speedyButton )
		controller.mouseListeners.append( self.firehoseButton )
		controller.mouseListeners.append( self.sharpshooterButton )
		controller.mouseListeners.append( self.debugButton )
		mvcState.GetView().ModelStarted(self)

	def Quit( self ):
		#print 'mm quitting'
		controller = mvcState.GetController()
		controller.mouseListeners.remove( self.freestyleButton )
		controller.mouseListeners.remove( self.freestyleTrickyButton )
		controller.mouseListeners.remove( self.speedyButton )
		controller.mouseListeners.remove( self.firehoseButton )
		controller.mouseListeners.remove( self.sharpshooterButton )
		controller.mouseListeners.remove( self.debugButton )
		if not self.nextModelClass:
			self.nextModelClass = SystemQuitFlag
		newModel = self.nextModelClass()
		mvcState.SetModel( newModel )

	def Freestyle( self ):
		#TODO: hack alert
		self.btnGroup.add( self.loadingButton )
		self.Draw()
		self.nextModelClass = FreestyleModel
		self.Quit()
	def FreestyleTricky( self ):
		#TODO: hack alert
		self.btnGroup.add( self.loadingButton )
		self.Draw()
		self.nextModelClass = FreestyleTrickyModel
		self.Quit()
	def Debug( self ):
		#TODO: hack alert
		self.btnGroup.add( self.loadingButton )
		self.Draw()
		self.nextModelClass = DebugModel
		self.Quit()
	def Speedy( self ):
		#TODO: hack alert
		self.btnGroup.add( self.loadingButton )
		self.Draw()
		self.nextModelClass = SpeedyModel
		self.Quit()
	def Sharpshooter( self ):
		#TODO: hack alert
		self.btnGroup.add( self.loadingButton )
		self.Draw()
		self.nextModelClass = SharpshooterModel
		self.Quit()
	def Firehose( self ):
		#TODO: hack alert
		self.btnGroup.add( self.loadingButton )
		self.Draw()
		self.nextModelClass = FirehoseModel
		self.Quit()

	def Loading( self ):
		pass
class MainMenuFlag:
	pass

class SystemQuitFlag:
	pass

class WinScreenModel:
	def __init__( self, time, money ):
		log.debug( 'made winscreen with '+ str( (time,money) ) )	
		self.nextModelClass = MainMenuFlag
		self.time = time
		self.money = money

	def Start( self ):
		mvcState.GetView().ModelStarted(self)
		controller = mvcState.GetController()
		controller.gameEventListeners.append( self )

	def Quit( self ):
		#print 'mm quitting'
		newModel = self.nextModelClass()
		mvcState.SetModel( newModel )

		controller = mvcState.GetController()
		controller.gameEventListeners.remove( self )

	def OnUserQuit( self ):
		self.Quit()

	def Update( self, timeChange ):
		pass


class WinScreenView(View):
	def __init__( self, screen, display ):
		self.screen = screen
		self.screenRect = screen.get_rect()
		self.display = display

		self.model = None

		self.bgImage = load_png( 'bg_winscreen.png' )

		self.btnGroup = RenderUpdates()

		quitBtn = QuitButton()
		quitBtn.rect.bottomleft = self.screenRect.bottomleft
		quitBtn.rect.move_ip( 10, -10 )
		self.btnGroup.add( quitBtn )
		self.quitButton = quitBtn

		self.groups = [ self.btnGroup ]

	def ModelStarted( self, model ):
		View.ModelStarted(self,model)

		controller = mvcState.GetController()
		controller.mouseListeners.append( self.quitButton )

		time = self.model.time/1000
		self.timeButton = MoneyWidget( time )
		self.timeButton.rect.topleft = (503,112)
		self.btnGroup.add( self.timeButton )

		money = self.model.money
		self.moneyButton = MoneyWidget( money )
		self.moneyButton.rect.topleft = (240,180)
		self.btnGroup.add( self.moneyButton )

		gay = rng.choice( [7, 11, 23, 29, 71, 93] )
		self.gayButton = MoneyWidget( gay )
		self.gayButton.rect.topleft = (328,432)
		self.btnGroup.add( self.gayButton )

	def Update( self, timeChange ):
		self.btnGroup.update( timeChange )

	def Kill( self ):
		controller = mvcState.GetController()
		controller.mouseListeners.remove( self.quitButton )
		self.btnGroup.empty()

	def OnUserQuit( self ):
		self.Kill()

class DebugModel(FreestyleModel):
	def _ImportSettings(self):
		import settings_debug as s_d
		for attrName in dir(s_d):
			setattr( settings, attrName, getattr(s_d,attrName) )

class FreestyleTrickyModel(FreestyleModel):
	def _ImportSettings(self):
		import settings_tricky as s
		for attrName in dir(s):
			setattr( settings, attrName, getattr(s,attrName) )

class SpeedyModel(FreestyleModel):
	def _ImportSettings(self):
		import settings_speedy as s
		for attrName in dir(s):
			setattr( settings, attrName, getattr(s,attrName) )
class SharpshooterModel(FreestyleModel):
	def _ImportSettings(self):
		import settings_sharpshooter as s
		for attrName in dir(s):
			setattr( settings, attrName, getattr(s,attrName) )
class FirehoseModel(FreestyleModel):
	def _ImportSettings(self):
		import settings_firehose as s
		for attrName in dir(s):
			setattr( settings, attrName, getattr(s,attrName) )

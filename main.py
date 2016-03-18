#!/usr/bin/env python
#Import Modules
#import SiGL
import pygame
import mvcState
from pygame.locals import *
from model import FreestyleModel, GameView, MainMenu, MainMenuFlag, WinScreenModel, WinScreenView, SystemQuitFlag

from log import log

RESOLUTION = (800,600)

from utils import load_sound
from random import Random
rng = Random()
class SoundManager:
	def __init__(self):
		controller = mvcState.GetController()
		controller.gameEventListeners.append( self )

		self.timeSinceSound = 0

		self.shootSounds = [
		                    load_sound( 'geyser00.ogg' ),
		                    load_sound( 'geyser01.ogg' ),
		                   ]
		self.ventSounds = [
		                    load_sound( 'geyser02.ogg' ),
		                    load_sound( 'geyser03.ogg' ),
		                   ]
		self.chaChing = load_sound('chaching.ogg')
		self.win = load_sound('win.ogg')

	def OnBladderShoot( self, power, height ):
		if self.timeSinceSound < 1000:
			return
		sound = rng.choice( self.shootSounds )
		sound.play()
		self.timeSinceSound = 0
	def OnBladderVent( self, power, height ):
		if self.timeSinceSound < 1000:
			return
		sound = rng.choice( self.ventSounds )
		sound.play()
		self.timeSinceSound = 0

	def OnDropOverCapacity(self, colorName):
		self.chaChing.play()

	def OnWin(self, foo, bar):
		self.win.play()


	def Update( self, timeChange ):
		self.timeSinceSound += timeChange
		
		
class DefaultController:
	def __init__(self):
		self.mouseListeners = []
		self.keyListeners = []
		self.gameEventListeners = []
	def HandlePygameEvents(self):
		events = pygame.event.get()
		view = mvcState.GetView()
		model = mvcState.GetModel()
		for event in events:
			if event.type == QUIT:
				#model.Quit()
				mvcState.SetModel( SystemQuitFlag() )
			elif event.type == KEYDOWN and event.key == K_ESCAPE:
				model.Quit()
			elif event.type == KEYDOWN:
				#KeyDown( event )
				pass
			elif event.type == KEYUP:
				#KeyUp( event )
				pass
			elif event.type == MOUSEBUTTONDOWN:
				for listener in self.mouseListeners:
					listener.OnMouseDown( event.pos ) 
			elif event.type == MOUSEBUTTONUP:
				for listener in self.mouseListeners:
					listener.OnMouseUp( event.pos ) 
			elif event.type == MOUSEMOTION:
				for listener in self.mouseListeners:
					listener.OnMouseMove( event ) 

	def GameEvent(self, gameEvent, *extraArgs):
		#log.debug( 'game event:'+ gameEvent +str(extraArgs) )
		#TODO: note: this suffers from the ACB event out-of-order bug
		#TODO: hack here to prevent list changing size during iteration
		listeners = self.gameEventListeners[:]
		for listener in listeners:
			methodName = 'On'+gameEvent
			if hasattr( listener, methodName ):
				method = getattr( listener, methodName )
				method( *extraArgs ) 

	
#-----------------------------------------------------------------------------
def main():
	"""this function is called when the program starts.
	   it initializes everything it needs, then runs in
	   a loop until the function returns."""


	#Initialize Everything
	global screen
	screen = None
	pygame.init()
	screen = pygame.display.set_mode(RESOLUTION)
	pygame.display.set_caption('Steam Jet Blower')
	#pygame.mouse.set_visible(0)


	#Prepare Game Objects

	#main menu handles the responsibilities of both: M and V
	model = MainMenu( screen, pygame.display )
	mvcState.SetModel( model )

	controller = DefaultController()
	mvcState.SetController( controller )

	view = None

	sMangr = SoundManager()

	#Main Loop
	clock = pygame.time.Clock()
	oldfps = 0
	while 1:
		timeChange = clock.tick(40)
		newfps = int(clock.get_fps())
		#if newfps != oldfps:
			#print "fps: ", newfps
			#oldfps = newfps

		if mvcState.justChanged:
			model = mvcState.GetModel()
			log.debug( 'state was jsut changed' )
			if mvcState.GetModel() == None \
			  or isinstance( mvcState.GetModel(), SystemQuitFlag ):
				log.debug( 'quittin' )
				break
			if isinstance( mvcState.GetModel(), MainMenuFlag ):
				log.debug( 'flagged for MM' )
				model = MainMenu( screen, pygame.display )
				mvcState.SetModel( model )
				view = model
				mvcState.SetView( view )
			elif isinstance( model, FreestyleModel ):
				view = GameView(screen,pygame.display)
				mvcState.SetView( view )
			elif isinstance( model, WinScreenModel ):
				view = WinScreenView(screen,pygame.display)
				mvcState.SetView( view )
			elif isinstance( model, MainMenu ):
				view = model
				mvcState.SetView( view )
			mvcState.justChanged = False
			#print 'calling start() on', model
			model.Start()

		#Handle Keyboard / Mouse Input Events
		controller.HandlePygameEvents()

		#if the mvcState changed because of some event, skip next steps
		if mvcState.justChanged:
			continue

		#Clear Everything
		view.Clear()

		#Update 
		view.Update( timeChange )
		model.Update( timeChange )
		sMangr.Update( timeChange )

		#if the mvcState changed because of the update, skip next steps
		if mvcState.justChanged:
			continue

		#Draw Everything
		view.Draw()


	#Game Over
	log.debug( "Game is over" )

	pygame.quit()

#this calls the 'main' function when this script is executed
if __name__ == '__main__': 
	import profile
	profile.run( 'main()' )
	#main()

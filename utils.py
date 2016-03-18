#!/usr/bin/env python
#Import Modules
import os, pygame 
from copy import copy
from pygame.locals import *
from log import log

datadir = 'data'
COLORS = { 
          'red': (255,0,0),
          'orange': (255,90,0),
          'yellow': (204,255,0),
          'green': (0,255,24),
          'blue': (0,0,255),
          'violet': (255,0,240),
}

_cachedPngs = {}

#-----------------------------------------------------------------------------
def load_png(name, extradirs=None):
	global _cachedPngs
	if extradirs:
		fullname = os.path.join(datadir, extradirs, name)
	else:
		fullname = os.path.join(datadir, name)

	if _cachedPngs.has_key( fullname ):
		image = _cachedPngs[fullname]
	else:
		try:
			image = pygame.image.load(fullname)
			if image.get_alpha is None:
				image = image.convert()
			else:
				image = image.convert_alpha()
			_cachedPngs[fullname] = image
		except pygame.error, message:
			log.debug( ' Cannot load image: '+ fullname )
			log.debug( 'Raising: '+ str(message) )
			raise message
	return image

#-----------------------------------------------------------------------------
def load_sound(name, extradirs=None):
	if extradirs:
		fullname = os.path.join(datadir, extradirs, name)
	else:
		fullname = os.path.join(datadir, name)

	class NoneSound:
		def play(self): pass

	if not pygame.mixer or not pygame.mixer.get_init():
		return NoneSound()

	try:
		sound = pygame.mixer.Sound(fullname)
	except pygame.error, message:
		log.debug( 'Cannot load sound: '+ fullname )
		raise pygame.error, message
	return sound

#-----------------------------------------------------------------------------
def change_alpha(origImg, newAlpha):
	if newAlpha < 0 or newAlpha > 255:
		raise Exception( "change_alpha: Alpha value out of range" )
	alphaArray = pygame.surfarray.pixels_alpha( origImg )
	for i in xrange( len(alphaArray) ):
		alphaArray[i] = newAlpha
	del alphaArray #this unlocks the surface

#-----------------------------------------------------------------------------
def change_alpha_mult(origImg, deltaAlpha):
	if deltaAlpha < 0 or deltaAlpha > 1:
		raise Exception( "change_alpha: Alpha value out of range" )
	alphaArray = pygame.surfarray.pixels_alpha( origImg )
	for i in xrange( len(alphaArray) ):
		alphaArray[i] = [ deltaAlpha*x for x in alphaArray[i] ]
	del alphaArray #this unlocks the surface


	

#this calls the 'main' function when this script is executed
if __name__ == '__main__': print "didn't expect that!"

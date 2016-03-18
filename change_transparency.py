#!/usr/bin/env python
#Import Modules
import pygame
from pygame.locals import *

_cachedOriginals = {}
_cachedCalculatedArrays = {}

#-----------------------------------------------------------------------------
def change_alpha_mult(img, percentAlpha):
	global _cachedOriginals
	global _cachedCalculatedArrays
	if percentAlpha < 0 or percentAlpha > 100 or type(percentAlpha) != int:
		raise Exception( "percentAlpha not an int between 0 and 100" )
	floatAlpha = float(percentAlpha) / 100
	alphaArray = pygame.surfarray.pixels_alpha( img )

	if not _cachedOriginals.has_key( id(img) ):
		origArray = alphaArray
		_cachedOriginals[id(img)] = alphaArray[:]
	else:
		origArray = _cachedOriginals[id(img)]

	key = ( percentAlpha, id(img) )
	if _cachedCalculatedArrays.has_key( key ):
		alphaArray = _cachedCalculatedArrays[ key ][:]
	else:
		for i in xrange( len(alphaArray) ):
			alphaArray[i] = [ floatAlpha*x for x in origArray[i] ]
		_cachedCalculatedArrays[ key ] = alphaArray[:]

	del alphaArray #this unlocks the surface


	

#this calls the 'main' function when this script is executed
if __name__ == '__main__': print "didn't expect that!"

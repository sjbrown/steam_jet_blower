#! /usr/bin/python

justChanged = False

_model = None
_view = None
_controller = None

def GetModel():
	global _model
	return _model
def SetModel( newModel ):
	global _model
	global justChanged
	_model = newModel
	justChanged = True
	#print 'juschango', newModel


def GetView():
	global _view
	return _view
def SetView( newView ):
	global _view
	global justChanged
	_view = newView
	justChanged = True
	#print 'juschangv', newView

def GetController():
	global _controller
	return _controller
def SetController( newController ):
	global _controller
	global justChanged
	_controller = newController
	justChanged = True
	#print 'juschangc', newController

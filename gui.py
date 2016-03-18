from poutine import gui_widgets
from utils import load_png

class ImgButton(gui_widgets.ButtonSprite):
	def __init__( self, name, onClickCallback=None, callbackArgs=() ):
		gui_widgets.Widget.__init__( self, None )
		self.onImg = load_png( name+'_on.png' )
		self.offImg = load_png( name+'_off.png' )
		self.hiImg = load_png( name+'_hi.png' )

		self.onClickCallback = onClickCallback
		self.callbackArgs = callbackArgs

		self.image = self.offImg
		self.rect = self.image.get_rect()

	#----------------------------------------------------------------------
        def update(self):
                if not self.dirty:
                        return

                if self.focused:
			img = self.onImg
                elif self.highlighted:
                        img = self.hiImg
                else:
                        img = self.offImg
                self.image = img

                self.dirty = 0

	#----------------------------------------------------------------------
        def OnMouseDown(self, pos):
		if self.rect.collidepoint( pos ):
			self.SetFocus( 1 )
	#----------------------------------------------------------------------
        def OnMouseUp(self, pos):
		if self.rect.collidepoint( pos ):
			self.Click()
	#----------------------------------------------------------------------
        def OnMouseMove(self, event):
		gui_widgets.ButtonSprite.OnMouseMove( self, event.pos )
		if not self.rect.collidepoint( event.pos ):
			self.SetFocus( 0 )

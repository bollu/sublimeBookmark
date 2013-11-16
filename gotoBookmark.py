import sublime, sublime_plugin
from pickle import dump, load
import threading 

from . import common

class GotoBookmarkCommand(sublime_plugin.WindowCommand, common.baseBookmarkCommand):
	def __init__(self, window):
		self.thread = None
		common.baseBookmarkCommand.__init__(self, window)


	def run(self):
		 if self.thread is not None:
		 	self.thread.join()

		 self.thread = GotoBookmarkHandler(self.window, self)
		 self.thread.start()

	#accessed by others
	def getBookmarkNames_(self):
		self.load_()

		bookmarkNames = []
		for bookmark in self.bookmarks:
			bookmarkNames.append(bookmark.getName())
		return bookmarkNames

	#accessed by others
	def getBookmark(self, index):
		if index == -1:
			return None

		else:
			return self.bookmarks[index]


class GotoBookmarkHandler(threading.Thread):
	def __init__(self, window, GotoBookmarkCommand):
		self.window = window
		self.GotoBookmarkCommand = GotoBookmarkCommand
		self.done = False

		self.fileSwitcher = FileSwitcher(window, GotoBookmarkCommand) 

		threading.Thread.__init__(self)  


		
	def run(self):

		view = self.window.active_view()
		items = self.GotoBookmarkCommand.getBookmarkNames_()
	
		self.window.show_quick_panel(items, self.Done_, sublime.MONOSPACE_FONT, 1, self.Highlighted_)


	def Done_(self, item):

		if item == -1:
			self.fileSwitcher.resetFile()
			common.gLog("Cancelled")
		else:
			self.fileSwitcher.switchFile(item)
			common.gLog("Done_")

		


	def Highlighted_(self, item):
		self.fileSwitcher.switchFile(item)
		common.gLog("Highlighted_")



class FileSwitcher:
	def __init__(self, window, GotoBookmarkCommand):
		self.window = window

		#keep a reference to the original file
		self.originalFile = common.Bookmark(window, "originalFile")

		self.GotoBookmarkCommand = GotoBookmarkCommand


	def resetFile(self):
		self.gotoBookmark(self.originalFile)


	def switchFile(self, index):
		bookmark = self.GotoBookmarkCommand.getBookmark(index)
		
		if bookmark is None:
			return

		self.gotoBookmark(bookmark)


	def gotoBookmark(self, bookmark):
		filePath = bookmark.getFilePath()
		row = bookmark.getRow()
		col = bookmark.getCol()

		#first open the file
		self.window.open_file(filePath)
		view = self.window.active_view()

		#now goto line
		pt = view.text_point(row, col)

		view.sel().clear()
		view.sel().add(sublime.Region(pt))

		view.show(pt)
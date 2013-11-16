import sublime, sublime_plugin
from pickle import dump, load
import threading 

from . import common

class AddBookmarkCommand(sublime_plugin.WindowCommand, common.baseBookmarkCommand):
	def __init__(self, window):
		self.thread = None
		common.baseBookmarkCommand.__init__(self, window)
		self.load_()

	def run(self):
		if self.thread is not None:
			self.thread.join()

		self.thread = AddBookmarkHandler(self.window, self)
		self.thread.start()

	#exposed to others 	
	def AddBookmark_(self, name):
		bookmark = common.Bookmark(self.window, name)
		bookmark.printDbg()

		self.bookmarks.append(bookmark)

		self.save_()
		


class AddBookmarkHandler(threading.Thread):
	def __init__(self, window, addBookmarkCommand):
		self.window = window
		self.addBookmarkCommand = addBookmarkCommand
		self.done = False

		threading.Thread.__init__(self)  
		
		

	def run(self):
		view = self.window.active_view()
		defaultString = "bookmark name"

		self.window.show_input_panel("Add Bookmark", defaultString, self.Done_, None, self.Cancel_)
	
	def Cancel_(self):
		self.done = True

		common.gLog("Add Cancelled")

		return

	def Done_(self, viewString):
		self.done = True
		self.addBookmarkCommand.AddBookmark_(viewString)
		return
		
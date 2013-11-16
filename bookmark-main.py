import sublime, sublime_plugin
from pickle import dump, load
from time import sleep





class SaveBookmarkCommand(sublime_plugin.WindowCommand):
	def __init__(self, window):
		self.window = window
		self.bookmarks = []
		self.dbg = True

	def run(self):
		try:
			pickleFile = open(savePath, 'wb')
			pickle.dump(self.bookmarks, pickleFile)
		except IOError:
			self.log ("Error: can\'t find file or read data")


import sublime, sublime_plugin, pickle
from pickle import dump, load


#gSavePath =  "bookmarks.pickle" 
gSavePath = "/home/bollu/bookmarks.pickle"

def gLog(str):
	if(True):
		print (str)



class Bookmark:
	def __init__(self, window, name):
		view = window.active_view()
		
		(row,col) = view.rowcol(view.sel()[0].begin())

		#caution: calculated from (0,0) NOT (1,1)
		self.filePath = view.file_name()
		self.row = row
		self.col = col
		self.name = name


	def Goto(self, window):
		print ("goto")
		window.open_file(self.filePath)

	def getRow(self):
		return self.row

	def getCol(self):
		return self.col

	def getName(self):
		return self.name

	def getFilePath(self):
		return self.filePath
		
	def printDbg(self):
		gLog ("Bookmark: name: " + self.name + "; row " + str(self.row) + "; column: " + str(self.col))


class baseBookmarkCommand:
	def __init__(self, window):
		self.window = window
		self.bookmarks = []
		self.dbg = True


	def save_(self):
		gLog ("saving")

		try:
			pickleFile = open(gSavePath, 'wb')
			pickle.dump(self.bookmarks, pickleFile)
			gLog("Saved")
		except IOError:
			gLog ("Error: can\'t find file or read data")


	def load_(self):
		gLog ("loading")

		try:
			pickleFile = open(gSavePath, 'rb')
			self.bookmarks = pickle.load(pickleFile)

			
		except IOError:
			gLog ("Error: can\'t find file or read data")
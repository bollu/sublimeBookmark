import sublime, sublime_plugin, pickle
from pickle import dump, load


#gSavePath =  "bookmarks.pickle" 
gSavePath = "/home/bollu/bookmarks.pickle"
gRegionTag = "sublime_Bookmarks"

global gBookmarks__
gBookmarks__ = [] 

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

		self.view = view
	
	def Goto(self, window, useColumnInfo):
		gLog ("goto")
		window.open_file(self.filePath)

		view = window.active_view()

		if useColumnInfo:
			pt = view.text_point(self.row, self.col)
		else:
			pt = view.text_point(self.row, 0)
			
		view.sel().clear()
		view.sel().add(sublime.Region(pt))

		view.show(pt)

	def getLine(self):
		gLog ("getLine")
		
		pt = self.view.text_point(self.row, self.col)
		lineRegion =  self.view.line(pt)
		lineText = self.view.substr(lineRegion)

		return ' '.join(lineText.split())

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
		gPersist.setBookmarks(self.bookmarks)


	def load_(self):
		gLog ("loading")
		self.bookmarks = gPersist.getBookmarks()




class Persistence:
	def __init__(self):
		self.loaded = False
		pass

	def getBookmarks(self):
		global gBookmarks__

		if not self.loaded:
			self.loaded = True

			gLog("\tloading bookmarks from file. should be one-time")

			pickleFile = open(gSavePath, 'rb')
			gBookmarks__ = pickle.load(pickleFile)

			for bookmark in gBookmarks__:
				bookmark.printDbg()

		return gBookmarks__


	def setBookmarks(self, bookmarks):
		global gBookmarks__

		#removeBookmarks and addBookmarks calls these functions
		gBookmarks__ = bookmarks



	def writeToDisk(self):
		global gBookmarks__

		pickleFile = open(gSavePath, 'wb')
		pickle.dump(gBookmarks__, pickleFile)

		gLog("\twriting bookmarks to disk. may take time.")


#this is hacky, but I'm new to python. Dunno a better way :(
global gPersist
gPersist = Persistence()


def updateGutter(view):
	global gPersist

	filePath = view.file_name()
	bookmarks = gPersist.getBookmarks()

	regions =  []
	for bookmark in bookmarks:
		if bookmark.getFilePath() == filePath:
			pt = view.text_point(bookmark.getRow(), 0)
			regions.append(sublime.Region(pt))

	view.erase_regions(gRegionTag)
	view.add_regions(gRegionTag, regions, scope="string", icon="bookmark", flags= sublime.PERSISTENT | sublime.DRAW_STIPPLED_UNDERLINE ) 
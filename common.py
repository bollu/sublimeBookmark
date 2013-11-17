import sublime, sublime_plugin
import pickle
from pickle import dump, load
from os.path import dirname

#gSavePath =  "bookmarks.pickle" 
gRelSavePath = '/Local/sublimeBookmarks.pickle'
#gSavePath = dirname(sublime.packages_path()) + gRelSavePath
global gSavePath 
gSavePath = dirname(sublime.packages_path())+'/Settings/sublimeBookmarks.pickle'

global gRegionTag
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

		global gSavePath
		gSavePath = dirname(sublime.packages_path())+'/Settings/sublimeBookmarks.pickle'
		#global gSavePath
		#gLog("\n\n gSavePAth::::: " + gSavePath)
		#gSavePath = dirname(sublime.packages_path()) + gRelSavePath

	def setSavePath(self):
		global gSavePath
		gSavePath = sublime.packages_path() +'/../Local/sublimeBookmarks.pickle'


	def getBookmarks(self):
		global gBookmarks__

		if not self.loaded:
			self.loaded = True

			global gSavePath
			gLog("\tloading bookmarks from file :" + gSavePath + ":. should be one-time")

			self.setSavePath();
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
		global gSavePath

		self.setSavePath();
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
	view.add_regions(gRegionTag, regions, scope="string", icon="bookmark")#, flags= sublime.PERSISTENT | sublime.DRAW_STIPPLED_UNDERLINE ) 



#panel creation code----------------------------

def capStringEnd(string, length):
		return string if len(string) <= length else string[ 0 : length - 3] + '...'


def capStringBegin(string, length):
		return string if len(string) <= length else '...' + string[ len(string) + 3 - (length)  : len(string) ] 



def createBookmarksPanelItems(bookmarks):
		bookmarkItems = []

		for bookmark in bookmarks:
			bookmarkName = bookmark.getName()
			bookmarkLine = capStringEnd(bookmark.getLine(), 50)
			bookmarkFile = capStringBegin(bookmark.getFilePath(), 50)

			bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )

		return bookmarkItems
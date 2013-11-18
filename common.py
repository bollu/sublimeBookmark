import sublime, sublime_plugin
import pickle
from pickle import dump, load
from os.path import dirname, isfile

gSavePath = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'
gRegionTag = "sublime_Bookmarks"

global gBookmarks
gBookmarks = None



def gLog(str):
	if(True):
		print ("\n" + str)

def getCurrentProject(window):
	project = window.project_file_name()
	if project is None:
		return ""
	return project


class Bookmark:
	def __init__(self, window, name):
		view = window.active_view()
		self.view = view

		self.name = name
		self.filePath = view.file_name()

		#subl is weird. It sets project_file_name() to None -_-
		self.project = getCurrentProject(window)

		#caution: calculated from (0,0) NOT (1,1)
		(row,col) = view.rowcol(view.sel()[0].begin())
		self.row = row
		self.col = col

		
	def Goto(self, window, useColumnInfo):
		rowColStr = ":" + str(self.row) + ":" + str(self.col)
		window.open_file(self.filePath + rowColStr, sublime.TRANSIENT | sublime.ENCODED_POSITION)

	def getLine(self):
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
	
	def getProject(self):
		return self.project


	def printDbg(self):
		gLog ("New Bookmark: " + self.name + " | " + str(self.row) + ": " + str(self.col) + "| Project: " + self.project)



#baseBookmarkCommand-------------------------------------
class baseBookmarkCommand:
	def __init__(self, window):
		self.window = window
		self.bookmarks = None

	def save_(self):
		setBookmarks(self.bookmarks)
	
	def load_(self):
		self.bookmarks = getBookmarks()

#save / load code----------------------------------------
def getBookmarks():
	global gBookmarks  #<- only need this when writing to a global

	gSavePath = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'

	#The first time sublime text loads, gBookmarks will be None. So, load bookmarks

	if gBookmarks is not None:
		return gBookmarks

	readBookmarksFromDisk()
	
	return gBookmarks

def setBookmarks(bookmarks):
	global gBookmarks

	assert bookmarks != None, "trying to write  *None* bookmarks."

	gBookmarks = bookmarks
	gLog("set global bookmarks")

def writeBookmarksToDisk():
	global gBookmarks
	global gSavePath

	assert gBookmarks != None, "trying to write *None* bookmarks to disk"

	gSavePath = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'
	
	pickleFile = open(gSavePath, "wb")
	pickle.dump(gBookmarks, pickleFile)

	gLog("wrote bookmarks to disk. Path: " + gSavePath)

def readBookmarksFromDisk():
	global gBookmarks
	global gSavePath

	gSavePath = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'

	if isfile(gSavePath):
		gLog("loading bookmarks from disk. Path: " + gSavePath)
		pickleFile = open(gSavePath, "rb")
		gBookmarks = pickle.load(pickleFile)

	else:
		gLog("no bookmark load file found. Path:" + gSavePath)
		gBookmarks = []

#Gutters-------------------------------------

def updateGutter(view):
	currentProject = getCurrentProject(view.window())

	filePath = view.file_name()
	bookmarks = getBookmarks()

	regions =  []
	for bookmark in bookmarks:
		if bookmark.getFilePath() == filePath:
			pt = view.text_point(bookmark.getRow(), 0)
			regions.append(sublime.Region(pt))

	view.erase_regions(gRegionTag)
	view.add_regions(gRegionTag, regions, scope="string", icon="bookmark")



#panel creation code----------------------------

def capStringEnd(string, length):
		return string if len(string) <= length else string[ 0 : length - 3] + '...'


def capStringBegin(string, length):
		return string if len(string) <= length else '...' + string[ len(string) + 3 - (length)  : len(string) ] 


def createBookmarksPanelItems(window, bookmarks):
		currentProject = getCurrentProject(window)

		bookmarkItems = []
		gLog("currentProject: " + currentProject)

		for bookmark in bookmarks:
			bookmarkProject = bookmark.getProject()
		
			bookmark.printDbg()

			#this is not yet perfect. will have to revise this
			if True or (currentProject == "") or (currentProject.lower() == bookmarkProject.lower()):
				bookmarkName = bookmark.getName()
				bookmarkLine = capStringEnd(bookmark.getLine(), 50)
				bookmarkFile = capStringBegin(bookmark.getFilePath(), 50)

				bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )
				
		return bookmarkItems
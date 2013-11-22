import sublime, sublime_plugin
from pickle import dump, load
from os.path import dirname, isfile

gSavePath = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'
gRegionTag = "sublime_Bookmarks_"


global gBookmarks
gBookmarks = None

global gIndex
gIndex = 0



def gLog(str):
	if(False):
		print ("\n" + str)
 
 
#Bookmark related code-----------------------------------------------------
def getCurrentProjectPath(window):
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
		
		global gIndex
		self.index = gIndex
		gIndex = gIndex + 1

		#subl is weird. It sets project_file_name() to None -_-
		self.projectPath = getCurrentProjectPath(window)


		#caution: calculated from (0,0) NOT (1,1)
		(row,col) = view.rowcol(view.sel()[0].begin())
		self.row = row				
		self.col = col

		pt = self.view.text_point(self.row, self.col)
		self.lineRegion =  self.view.line(pt)


	def __del__(self):
		self.remove()


	def __pGetRegionTag__(self):
		return gRegionTag + str(self.index)


	def goto(self, window, useColumnInfo):
		view = window.open_file(self.filePath) 
		view.show_at_center(self.lineRegion)


	def remove(self):
		self.view.erase_regions(self.__pGetRegionTag__())


	def mark_gutter(self):
		#overwrite the current region
		self.view.add_regions(self.__pGetRegionTag__(), [self.lineRegion], "text.plain", "bookmark", sublime.DRAW_NO_FILL)


	def get_line(self):
		lineText = self.view.substr(self.lineRegion)
		return ' '.join(lineText.split())


	def get_name(self):
		return self.name


	def get_file_path(self):
		return self.filePath
	

	def get_project_path(self):
		return self.projectPath


	def print_dbg(self):
		gLog ("Bookmark: " + self.name + " | " + str(self.row) + ": " + str(self.col) + "| Project: " + self.projectPath)

	

#BaseBookmarkCommand-------------------------------------
class BaseBookmarkCommand:
	def __init__(self, window):
		self.window = window


	def _save(self):
		set_bookmarks(self.bookmarks)
	

	def _load(self):
		self.bookmarks = get_bookmarks()

#save / load code----------------------------------------
def get_bookmarks():
	global gBookmarks  #<- only need this when writing to a global

	gSavePath = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'

	#The first time sublime text loads, gBookmarks will be None. So, load bookmarks
	if gBookmarks is not None:
		return gBookmarks


	_read_bookmarks_from_disk()
	return gBookmarks


def set_bookmarks(bookmarks):
	global gBookmarks

	assert bookmarks != None, "trying to write  *None* bookmarks."

	gBookmarks = bookmarks
	gLog("set global bookmarks")


def _write_bookmarks_to_disk():
	global gBookmarks
	global gSavePath
	global gIndex

	assert gBookmarks != None, "trying to write *None* bookmarks to disk"

	gSavePath = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'
	
	pickleFile = open(gSavePath, "wb")
	dump(gBookmarks, pickleFile)
	dump(gIndex, pickleFile)

	gLog("wrote bookmarks to disk. Path: " + gSavePath)


def _read_bookmarks_from_disk():
	global gBookmarks
	global gSavePath
	global gIndex

	gSavePath = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'

	if isfile(gSavePath):
		gLog("loading bookmarks from disk. Path: " + gSavePath)

		pickleFile = open(gSavePath, "rb")
		gBookmarks = load(pickleFile)
		gIndex = load(pickleFile)

		for bookmark in gBookmarks:
			bookmark.mark_gutter()
	else:
		gLog("no bookmark load file found. Path:" + gSavePath)
		gBookmarks = []


#panel creation code----------------------------

def _ellipsis_string_end(string, length):
		return string if len(string) <= length else string[ 0 : length - 3] + '...'


def _ellipsis_string_begin(string, length):
		return string if len(string) <= length else '...' + string[ len(string) + 3 - (length)  : len(string) ] 


def create_bookmarks_panel_items(window, bookmarks):
		currentProject = getCurrentProjectPath(window)

		bookmarkItems = []
		gLog("currentProject: " + currentProject)

		for bookmark in bookmarks:
			bookmarkProject = bookmark.get_project_path()
		
			bookmark.print_dbg()

			#this is not yet perfect. will have to revise this
			if True or (currentProject == "") or (currentProject.lower() == bookmarkProject.lower()):
				
				bookmarkName = bookmark.get_name()
				
				bookmarkLine = _ellipsis_string_end(bookmark.get_line(), 55)
				bookmarkFile = _ellipsis_string_begin(bookmark.get_file_path(), 55)

				bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )
				
		return bookmarkItems
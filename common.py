import sublime, sublime_plugin
from pickle import dump, load
from os.path import dirname, isfile

g_SAVE_PATH = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'
g_REGION_TAG = "sublime_Bookmarks_"


global g_BOOKMARK_LIST
g_BOOKMARK_LIST = None

global g_BOOKMARK_COUNT
g_BOOKMARK_COUNT = 0



def g_log(str):
	if(True):
		#dear lord, I'm a monster
		print ("\n\nLOG: " + str + "\n\n")
 

#Bookmark related code-----------------------------------------------------
def _get_current_project_path(window):
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
		self.projectPath = _get_current_project_path(window)

		#caution: calculated from (0,0) NOT (1,1)
		(row,col) = view.rowcol(view.sel()[0].begin())
		self.row = row				
		self.col = col

		pt = self.view.text_point(self.row, 0)
		self.lineRegion =  self.view.line(pt)

		global g_BOOKMARK_COUNT
		self.index = g_BOOKMARK_COUNT
		g_BOOKMARK_COUNT = g_BOOKMARK_COUNT + 1


	def __del__(self):
		self.remove()

	def goto(self, window, useColumnInfo):
		view = window.open_file(self.filePath) 
		view.show_at_center(self.lineRegion)


	def remove(self):
		self.view.erase_regions(self._get_region_tag())


	def mark_gutter(self):
		#overwrite the current region
		self.view.add_regions(self._get_region_tag(), [self.lineRegion], "text.plain", "bookmark", sublime.DRAW_NO_FILL)


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
		g_log ("Bookmark: " + self.name + " | " + str(self.row) + ": " + str(self.col) + "| Project: " + self.projectPath)


	def _get_region_tag(self):
		return g_REGION_TAG + str(self.index)

	

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
	global g_BOOKMARK_LIST  #<- only need this when writing to a global

	g_SAVE_PATH = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'

	#The first time sublime text loads, g_BOOKMARK_LIST will be None. So, load bookmarks
	if g_BOOKMARK_LIST is not None:
		return g_BOOKMARK_LIST


	_read_bookmarks_from_disk()
	return g_BOOKMARK_LIST


def set_bookmarks(bookmarks):
	global g_BOOKMARK_LIST

	assert bookmarks != None, "trying to write  *None* bookmarks."

	g_BOOKMARK_LIST = bookmarks
	g_log("set global bookmarks")


def _write_bookmarks_to_disk():
	global g_BOOKMARK_LIST
	global g_SAVE_PATH
	global g_BOOKMARK_COUNT

	#if the bookmarks haven't been loaded yet - 2 possibilities
	#1) no pickle file exists (this is the first execution. So chill)
	#2) _read_bookmarks_from_disk() hasn't been called yet
	#both are solved by calling _read_bookmarks_from_disk()
	if g_BOOKMARK_LIST == None:
		g_log("trying to write *None* bookmarks to disk")
		_read_bookmarks_from_disk()
		return

	g_SAVE_PATH = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'
	
	pickleFile = open(g_SAVE_PATH, "wb")
	dump(g_BOOKMARK_LIST, pickleFile)
	dump(g_BOOKMARK_COUNT, pickleFile)

	g_log("wrote bookmarks to disk. Path: " + g_SAVE_PATH)


def _read_bookmarks_from_disk():
	global g_BOOKMARK_LIST
	global g_SAVE_PATH
	global g_BOOKMARK_COUNT

	g_SAVE_PATH = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'

	if isfile(g_SAVE_PATH):
		g_log("loading bookmarks from disk. Path: " + g_SAVE_PATH)

		pickleFile = open(g_SAVE_PATH, "rb")
		g_BOOKMARK_LIST = load(pickleFile)
		g_BOOKMARK_COUNT = load(pickleFile)

		for bookmark in g_BOOKMARK_LIST:
			bookmark.mark_gutter()
	else:
		g_log("no bookmark load file found. Path:" + g_SAVE_PATH)
		g_BOOKMARK_LIST = []


#panel creation code----------------------------

def _ellipsis_string_end(string, length):
		return string if len(string) <= length else string[ 0 : length - 3] + '...'


def _ellipsis_string_begin(string, length):
		return string if len(string) <= length else '...' + string[ len(string) + 3 - (length)  : len(string) ] 


def create_bookmarks_panel_items(window, bookmarks):
		currentProject = _get_current_project_path(window)

		bookmarkItems = []
		g_log("currentProject: " + currentProject)

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
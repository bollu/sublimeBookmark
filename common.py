import sublime, sublime_plugin
from pickle import dump, load
from os.path import dirname, isfile

from . import fileLock
import sys

g_VERSION = "1.0.3"

#Holy crap Turing is rolling in his grave right now
#This is a monstrosity. Have to rewrite as an FSM or something.
#this is *worse* than spaghetti code.

g_SAVE_PATH = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'

def get_save_path():
	return dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'


g_REGION_TAG = "sublime_Bookmarks_"
g_SETTINGS_NAME = "SublimeBookmarks.sublime-settings"


g_BOOKMARK_LIST = None
g_BOOKMARK_COUNT = 0

g_SETTINGS_NAME = "SublimeBookmarks.sublime-settings" 

#settings
g_SETTINGS = {
	"show_free": True,
	"show_project": False
}


def g_log(str):
	if(True):
		#dear lord, I'm a monster
		print ("\nSublimeBookmarks log: " + str + "\n")
 
#Initialization------------------------------------------
def init(window):
	g_log("***INIT BOOKMARKS!****")
	load_settings()
	_read_bookmarks_from_disk(window)

	#mark the gutters
	for bookmark in g_BOOKMARK_LIST:
			bookmark.mark_gutter(window)


#Bookmark related code-----------------------------------------------------
def _get_current_project_path(window):
	project = window.project_file_name()
	if project is None:
		return ""
		
	return project


class Bookmark:
	def __init__(self, window, name, visible=True):

		self.name = name
		self.visible = visible

		view = window.active_view()

		#set up the unique ID part first :)
		global g_BOOKMARK_COUNT
		self.index = g_BOOKMARK_COUNT
		self.regionTag = g_REGION_TAG + str(self.index)

		g_BOOKMARK_COUNT = g_BOOKMARK_COUNT + 1

		self.filePath = view.file_name()
		self.projectPath = _get_current_project_path(window)
		
		#caution: calculated from (0,0) NOT (1,1)
		(self.row, self.col) = view.rowcol(view.sel()[0].begin())

		self.pt = view.text_point(self.row, 0)
		self.region =  view.line(self.pt)

		#to get the region, we have to mark first :)
		lineText = view.substr(self.region)
		self.line =  ' '.join(lineText.split())

		#mark gutter
		self.mark_gutter(window)


	def _getMyView(self, window):
		prevView = window.active_view()

		if prevView.file_name() == self.get_file_path():
			return prevView

		myView = window.open_file(self.filePath, sublime.TRANSIENT)
		window.focus_view(prevView)

		return myView

	def goto(self, window, useColumnInfo):
		view = window.open_file(self.filePath)

		#get your region 
		regions = view.get_regions(self.regionTag)

		#the region has been destroyed. recreate region and re-mark
		if not regions:
			g_log("*******unable to get my region!******")
			self.inflate(window)
			self.mark_gutter(window)

			#recursion!
			self.goto(window, useColumnInfo)
			return
		else:
			view.show_at_center(regions[0])

	def remove(self, window):
		self._getMyView(window).erase_regions(self.regionTag)


	def mark_gutter(self, window):
		myView = self._getMyView(window)
		
		if(self.visible and _should_display_bookmark(window, self)):
			#overwrite the current region
			myView.add_regions(self.regionTag, [self.region], "text.plain", "bookmark", sublime.PERSISTENT | sublime.DRAW_NO_FILL)
		else:
			myView.add_regions(self.regionTag, [self.region], "text.plain",  "", sublime.PERSISTENT | sublime.HIDDEN)

	def get_line(self):
		return self.line

	def get_name(self):
		return self.name


	def get_file_path(self):
		return self.filePath
	

	def get_project_path(self):
		return self.projectPath


	def print_dbg(self):
		g_log ("Bookmark: " + self.name + "| Project: " + self.projectPath)

	#Pickling Code (Copy pasted)---------------------------
	def deflate(self, window):
		#get my own point and update my row and column
		(self.row, self.col) = self._getMyView(window).rowcol(self.pt)

	def __getstate__(self):

		# Copy the object's state from self.__dict__ which contains
		# all our instance attributes. Always use the dict.copy()
		# method to avoid modifying the original state.
		state = self.__dict__.copy()
		return state

	def __setstate__(self, state):
		# Restore instance attributes (i.e., filename and lineno).
		self.__dict__.update(state)

	def inflate(self, window):
		myView = self._getMyView(window)

		self.pt = myView.text_point(self.row, self.col)
		self.region = myView.line(self.pt)


#BaseBookmarkCommand-------------------------------------
class BaseBookmarkCommand:
	def __init__(self, window):
		self.window = window


	def _save(self):
		set_bookmarks(self.bookmarks, self.window)
	

	def _load(self):
		self.bookmarks = get_bookmarks(self.window)
		load_settings()

#save / load code----------------------------------------
def get_bookmarks(window, shouldFilter=True):

	_read_bookmarks_from_disk(window)

	if shouldFilter:
		#return the list of *permissible* bookmarks. 
		return _create_bookmarks_list(window, g_BOOKMARK_LIST)
	else:
		return g_BOOKMARK_LIST


def set_bookmarks(bookmarks, window):
	g_log("set global bookmarks")
	
	global g_BOOKMARK_LIST

	assert bookmarks != None, "trying to write  *None* bookmarks."

	g_BOOKMARK_LIST = bookmarks
	_write_bookmarks_to_disk(window)

	

#IO-------------------------------------------------------------
def _write_bookmarks_to_disk(window):
	global g_BOOKMARK_LIST
	global g_SAVE_PATH
	global g_BOOKMARK_COUNT

	#if the bookmarks haven't been loaded yet - 2 possibilities
	#1) no pickle file exists (this is the first execution EVER. So chill)
	#2) _read_bookmarks_from_disk() hasn't been called yet (bookmarks have not
	# been loaded for the first time)
	#both are solved by calling _read_bookmarks_from_disk()
	if g_BOOKMARK_LIST == None:
		g_log("trying to write *None* bookmarks to disk")
		_read_bookmarks_from_disk(window)
		return

	
	for bookmark in g_BOOKMARK_LIST:
		bookmark.deflate(window)

	g_SAVE_PATH = get_save_path()
	


	with fileLock.FileLock(g_SAVE_PATH):

		try:
			pickleFile = open(g_SAVE_PATH, "wb")
		except  Exception:
			g_log('Error when opening pickle')
			_load_defaults()

		dump(g_VERSION, pickleFile)
		dump(g_BOOKMARK_LIST, pickleFile)
		dump(g_BOOKMARK_COUNT, pickleFile)

		g_log("wrote bookmarks to disk. Path: " + g_SAVE_PATH)

def _read_bookmarks_from_disk(window):
	global g_BOOKMARK_LIST
	global g_SAVE_PATH
	global g_BOOKMARK_COUNT

	g_log("reading bookmarks from disk")

	g_SAVE_PATH = get_save_path()

	if not isfile(g_SAVE_PATH):
		g_log("no bookmark load file found. Path:" + g_SAVE_PATH)
		_load_defaults()
		return

	g_log("loading bookmarks from disk. Path: " + g_SAVE_PATH)

	with fileLock.FileLock(g_SAVE_PATH):
		
		try:
			pickleFile = open(g_SAVE_PATH, "rb")

			pickleVersion = load(pickleFile)
			g_BOOKMARK_LIST = load(pickleFile)
			g_BOOKMARK_COUNT = load(pickleFile)

			if pickleVersion != g_VERSION:
				g_log("Older pickle Present:" + g_SAVE_PATH)
				_load_defaults()

			
			if g_BOOKMARK_LIST is None or g_BOOKMARK_COUNT is None:
				g_log("Unable to load pickle correctly:" + g_SAVE_PATH)
				_load_defaults()


			

		except  Exception:
			g_log('Error when opening pickle')
			_load_defaults()



	for bookmark in g_BOOKMARK_LIST:
		bookmark.inflate(window)

		
def _load_defaults():
	global g_BOOKMARK_LIST
	global g_BOOKMARK_COUNT

	g_BOOKMARK_LIST = []
	g_BOOKMARK_COUNT = 0


#Settings----------------------------------------------------------------------
def save_settings(window):
	pass

def load_settings():
	global g_SETTINGS

	g_log("loading settings")
	settings = sublime.load_settings(g_SETTINGS_NAME)

	#not a fan of hardcoding this
	g_SETTINGS["show_free"]  = settings.get("always_show_free_bookmarks", False)
	g_SETTINGS["show_project"] = settings.get("always_show_project_bookmarks", True)


#panel creation code----------------------------
def _ellipsis_string_end(string, length):
		#I have NO idea why the hell this would happen. But it's happening.
		if string is None:
			return ""
		else:
			return string if len(string) <= length else string[ 0 : length - 3] + '...'


def _ellipsis_string_begin(string, length):
		if string is None:
			return ""
		else:	
			return string if len(string) <= length else '...' + string[ len(string) + 3 - (length)  : len(string) ] 


def create_bookmarks_panel_items(window, bookmarks):	
		bookmarkItems = []

		for bookmark in bookmarks:

			bookmarkName = bookmark.get_name()
			bookmarkLine = _ellipsis_string_end(bookmark.get_line(), 55)
			bookmarkFile = _ellipsis_string_begin(bookmark.get_file_path(), 55)

			bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )

		return bookmarkItems

		# bookmarkItems = []
		# g_log("currentProject: " + currentProject)

		# for bookmark in bookmarks:
		# 	bookmarkProject = bookmark.get_project_path()
		
		# 	bookmark.print_dbg()

		# 	#this is not yet perfect. will have to revise this
		# 	if True or (currentProject == "") or (currentProject.lower() == bookmarkProject.lower()):
				
		# 		bookmarkName = bookmark.get_name()
				
		# 		bookmarkLine = _ellipsis_string_end(bookmark.get_line(), 55)
		# 		bookmarkFile = _ellipsis_string_begin(bookmark.get_file_path(), 55)

		# 		bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )
				
		# return bookmarkItems


def _should_display_bookmark(window, bookmark):
	currentProject = _get_current_project_path(window)
	bookmarkProject = bookmark.get_project_path()

	#if the bookmark has a project and *that project is open*,
		#show it.

	#if the bookmark was free and the editor *is now free*,
	#show it
	if currentProject == bookmarkProject:
		return True

	#if you should always free bookmarks and this bookmark
	#is free, add it
	elif g_SETTINGS["show_free"] == True and bookmarkProject == "":
		return True

	#if you should always show project related bookmarks and this bookmark
	#has a project, add it
	elif g_SETTINGS["show_project"] == True and bookmarkProject != "":
		return True

	else:
		return False


def _create_bookmarks_list(window, bookmarks):
	g_log("sorting bookmarks")

	currentProject = _get_current_project_path(window)
	g_log("current project: " + currentProject)

	bookmarksList = []

	for bookmark in bookmarks:


		bookmarkProject = bookmark.get_project_path()

		if _should_display_bookmark(window, bookmark):
			bookmarksList.append(bookmark)
		else:
			continue

			
	return bookmarksList

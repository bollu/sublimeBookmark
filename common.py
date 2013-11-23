import sublime, sublime_plugin
from pickle import dump, load
from os.path import dirname, isfile

from . import fileLock
import sys

#Holy crap Turing is rolling in his grave right now
#This is a monstrosity. Have to rewrite as an FSM or something.
#this is *worse* than spaghetti code.

g_SAVE_PATH = dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'
g_REGION_TAG = "sublime_Bookmarks_"


global g_BOOKMARK_LIST
g_BOOKMARK_LIST = None

global g_BOOKMARK_COUNT
g_BOOKMARK_COUNT = 0

global g_VERSION
g_VERSION = "1.0.1"

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
	def __init__(self, window, name, visible=True):
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
		self.region =  self.view.line(pt)


		global g_BOOKMARK_COUNT
		self.index = g_BOOKMARK_COUNT
		g_BOOKMARK_COUNT = g_BOOKMARK_COUNT + 1

		self.visible = visible
		self.mark_gutter()
		
	def __del__(self):
		self.remove()

	def goto(self, window, useColumnInfo):
		view = window.open_file(self.filePath) 
		view.show_at_center(self._get_personal_region())

	def remove(self):
		self.view.erase_regions(self._get_region_tag())


	def mark_gutter(self):
		if(self.visible):
			#overwrite the current region
			self.view.add_regions(self._get_region_tag(), [self.region], "text.plain", "bookmark", sublime.DRAW_NO_FILL)
		else:
			self.view.add_regions(self._get_region_tag(), [self.region], "text.plain",  "", sublime.HIDDEN)

	def get_line(self):
		lineText = self.view.substr(self._get_personal_region())
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

	def _get_personal_region(self):
		return self.view.get_regions(self._get_region_tag())[0]
	

	#Pickling Code (Copy pasted)
	def __getstate__(self):

		# Copy the object's state from self.__dict__ which contains
		# all our instance attributes. Always use the dict.copy()
		# method to avoid modifying the original state.
		state = self.__dict__.copy()
		return state

	def __setstate__(self, state):
		# Restore instance attributes (i.e., filename and lineno).
		self.__dict__.update(state)
		self.mark_gutter()
  

#BaseBookmarkCommand-------------------------------------
class BaseBookmarkCommand:
	def __init__(self, window):
		self.window = window


	def _save(self):
		set_bookmarks(self.bookmarks)
	

	def _load(self):
		self.bookmarks = get_bookmarks()

#save / load code----------------------------------------
def get_save_path():
	return dirname(sublime.packages_path()) + '/Local/sublimeBookmarks.pickle'

def get_bookmarks():
	global g_BOOKMARK_LIST  #<- only need this when writing to a global

	g_SAVE_PATH = get_save_path()

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

def _read_bookmarks_from_disk():
	global g_BOOKMARK_LIST
	global g_SAVE_PATH
	global g_BOOKMARK_COUNT

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

			for bookmark in g_BOOKMARK_LIST:
				bookmark.mark_gutter()

		except  Exception:
			g_log('Error when opening pickle')
			_load_defaults()

		
def _load_defaults():
	global g_BOOKMARK_LIST
	global g_BOOKMARK_COUNT

	g_BOOKMARK_LIST = []
	g_BOOKMARK_COUNT = 0


#panel creation code----------------------------

def _ellipsis_string_end(string, length):
		#I have NO idea why the hell this would happen. But it's happening
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
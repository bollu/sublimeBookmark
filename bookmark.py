from .common import *

class Bookmark:
	
	def __init__(self, uid, name, window, activeView):
		self.uid = int(uid)
		self.name = str(name)

		self.filePath = str(activeView.file_name())
		self.projectPath = getCurrentProjectPath(window)

		region = getCurrentLineRegion(activeView)
		self.regionA = int(region.a)
		self.regionB = int(region.b)
		
		self.group = getCurrentActiveGroup(window) 

		self.lineStr = activeView.substr(region)

		cursorPos = activeView.sel()[0].begin()
		self.lineNumber = activeView.rowcol(cursorPos)[0]

		
		self.bufferID = activeView.buffer_id()

	def getBufferID(self):
		return self.bufferID

		
	def getName(self):
		return self.name

	def getUid(self):
		return self.uid

	def getRegion(self):
		return sublime.Region(self.regionA, self.regionB)

	def getFilePath(self):
		return self.filePath

	def getProjectPath(self):
		return self.projectPath

	def getLineNumber(self):
		return self.lineNumber

	def getLineStr(self):
		return self.lineStr

	def getGroup(self):
		return self.group


	def setLineStr(self, newLineStr):
		self.lineStr = str(newLineStr)

	def setRegion(self, region):
		self.regionA = region.a
		self.regionB = region.b

	def setGroup(self, group):
		self.group = int(group)


	def isTemporary(self):
		return self.filePath == "None"



	def goto(self, window):
		view = getBookmarkView(window, self)
		assert (view is not None)

		region = self.getRegion()
		view.show_at_center(region)
			
		#move cursor to the middle of the bookmark's region
		bookmarkRegionMid = 0.5 * (region.begin() +  region.end())
		moveRegion = sublime.Region(bookmarkRegionMid, bookmarkRegionMid)
		view.sel().clear()
		view.sel().add(moveRegion)


	def isEmpty(self,  view):
		region = self.getRegion()

		line = view.substr(region) 
		return isLineEmpty(line)

	#the bookmark is associated with the current view
	def isMyView(self, window, view):
		#I bloody hate python for this madness
		if view is None:
			return False

		bufferID = view.buffer_id()
		filePath = view.file_name()

		if self.isTemporary():
			return self.getBufferID() == bufferID
		else:
			return  self.getFilePath() == filePath

	#updates the bookmark's data
	#1) moved region to cover whole line
	#2) updates the group info
	#3) updates the current line string
	def updateData(self, window, myView):
		regions = myView.get_regions(str(self.uid))

		#the region is not loaded yet
		if len(regions) == 0:
			return

		lines = myView.split_by_newlines(regions[0])

		region = lines[0]
		self.regionA = region.a
		self.regionB = region.b

		self.lineStr = myView.substr(region) 
		self.group = window.get_view_index(myView)[0]



def getBookmarkView(window, bookmark):
	view = None
	if bookmark.isTemporary():
		#mimic behavior of open_file. so w have to focus the view too...
		view = getViewByBufferID(window, bookmark.getBufferID())
		window.focus_view(view)
	else:
		view = window.open_file(bookmark.getFilePath())

	assert view is not None
	return view

def shouldRemoveTempBookmark(window, bookmark):
	assert(bookmark.isTemporary())
	return getViewByBufferID(window, bookmark.getBufferID()) is None


#I hate this function.
def moveBookmarkToGroup(window, bookmark, group):
	def moveViewToGroup(window, view, group):
		(viewGroup, viewIndex) = window.get_view_index(view) 


		#the view is not in the required group so move it
		#we have to move the view to the other group and give it a new index
		if group != viewGroup or viewGroup == -1 or viewIndex == -1:
			
			#SUBLIME_BUG
			#if the group the view is currently in has only one element - i.e  this view,
			#sublime text goes crazy and closes our options selector. So, we have to create
			#a new file in the old group and *only then* move the view.
			if len(window.views_in_group(viewGroup)) == 1:
				window.focus_group(viewGroup)
				window.new_file()


			#if there are 0 views, then the moved view will have index 0
			#similarly, if there are n views, the last view will have index (n-1), and
			#so the new view will have index n  
			newIndex = len (window.views_in_group(group))
			#move the view to the highlighted group and assign a
			#correct index
			window.set_view_index(view, group, newIndex)

		#the view is in the right group, so chill
		else:
			pass


	view = None

	if bookmark.isTemporary():
		view = getViewByBufferID(window, bookmark.getBufferID())
		assert (view is not None)
	
	else:
		view = window.open_file(bookmark.getFilePath())

	assert (view is not None)

	#move the bookmark's view to the correct group
	moveViewToGroup(window, view, group)

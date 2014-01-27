import sublime
from copy import deepcopy

class OptionsSelector:
	def __init__(self, window, panelItems, onDone, onHighlight):
		self.window = window
		self.panelItems = deepcopy(panelItems)
		self.onDone = onDone
		self.onHighlight = onHighlight
		
	def start(self):
		startIndex = 0
		self.window.show_quick_panel(self.panelItems, self.onDone, 0, startIndex, self.onHighlight)


class OptionsInput:
	def __init__(self, window, caption, initalText, onDone, onCancel):
		self.window = window
		self.caption = caption
		self.initalText = initalText
		self.onDone = onDone
		self.onCancel = onCancel

		
	def start(self):
		view = self.window.active_view()
		inputPanelView = self.window.show_input_panel(self.caption, self.initalText, self.onDone, None, self.onCancel)

		#select the text in the view so that when the user types a new name, the old name
		#is overwritten
		assert (len(inputPanelView.sel()) > 0)
		selectionRegion = inputPanelView.full_line(inputPanelView.sel()[0])
		inputPanelView.sel().add(selectionRegion)
	

def createBookmarkPanelItems(window, visibleBookmarks):	

	def ellipsisStringEnd(string, length):
		#I have NO idea why the hell this would happen. But it's happening.
		if string is None:
			return ""
		else:
			return string if len(string) <= length else string[ 0 : length - 3] + '...'


	def ellipsisStringBegin(string, length):
		if string is None:
			return ""
		else:	
			return string if len(string) <= length else '...' + string[ len(string) + 3 - (length)  : len(string) ] 


	bookmarkItems = []

	for bookmark in visibleBookmarks:
			bookmarkName = bookmark.getName()

			bookmarkLine = bookmark.getLineStr().lstrip()
			bookmarkFile = ellipsisStringBegin(bookmark.getFilePath().lstrip(), 55)
			
			bookmarkItems.append( [bookmarkName, bookmarkLine, bookmarkFile] )
		

	return bookmarkItems

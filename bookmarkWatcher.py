import sublime, sublime_plugin
import thread

class bookmarkWatcher(sublime_plugin.EventListener):
	def on_activated(self, view):
		sublime.active_window().run_command("sublime_bookmark", {"type": "mark_buffer" } )
		sublime.active_window().run_command("sublime_bookmark", {"type": "move_bookmarks" } )


	def on_modified(self, view):
		sublime.active_window().run_command("sublime_bookmark", {"type": "move_bookmarks" } ) 


	def on_deactivated(self, view):
		sublime.active_window().run_command("sublime_bookmark", {"type": "mark_buffer" } )
		sublime.active_window().run_command("sublime_bookmark", {"type": "move_bookmarks" } )

	#must be no close, not on pre close. on pre-close,the view still exists
	def on_close(self, view):
		sublime.active_window().run_command("sublime_bookmark", {"type": "update_temporary" } )

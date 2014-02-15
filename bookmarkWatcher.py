import sublime, sublime_plugin
import thread

class bookmarkWatcher(sublime_plugin.EventListener):
	def on_activated(self, view):
		window = sublime.active_window()

		if window is not None:
			window.run_command("sublime_bookmark", {"type": "mark_buffer" } )
			window.run_command("sublime_bookmark", {"type": "move_bookmarks" } )


	def on_modified(self, view):
		window = sublime.active_window()

		if window is not None:
			window.run_command("sublime_bookmark", {"type": "move_bookmarks" } ) 


	def on_deactivated(self, view):
		window = sublime.active_window()

		if window is not None:
			window.run_command("sublime_bookmark", {"type": "mark_buffer" } )
			window.run_command("sublime_bookmark", {"type": "move_bookmarks" } )

	#must be no close, not on pre close. on pre-close,the view still exists
	def on_close(self, view):
		window = sublime.active_window()

		if window is not None:
			window.run_command("sublime_bookmark", {"type": "update_temporary" } )

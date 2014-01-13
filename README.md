sublimeBookmark
===============

a better bookmark system for SublimeText

![demo gif](http://i.imgur.com/gtjChPG.gif)

Motivation
==========

Let's face it: sublime text's bookmark system __sucks__.
 __\<rant\>__
 It doesn't support named bookmarks. It doesn't save bookmark statuses, and it is just terrible to use overall.
  __\</rant\>__.

This is a replacement for sublime text's bookmark functionality. It's slicker and easier to use, and has way more features. 

**Note**: As of now, This is only for **Sublime Text 3**.


Features
========

* Named bookmarks
* Bookmarks are saved across sessions
* Goto any bookmark in the project
* Add any number of bookmarks (not just 12).
* Project based bookmarks (bookmarks are stored per-project and bookmarks can be navigated on a per-project basis)

To Install
==========

<!-- this is copy-pasted from sublimeCodeIntel. Thanks for the great description! -->

**With the Package Control plugin:** The easiest way to install SublimeBookmarks is through Package Control, which can be found at this site: http://wbond.net/sublime_packages/package_control

Once you install Package Control, restart Sublime Text and bring up the Command Palette (``Command+Shift+P`` on OS X, ``Control+Shift+P`` on Linux/Windows). Select "Package Control: Install Package", wait while Package Control fetches the latest package list, then select SublimeBookmarks when the list appears. The advantage of using this method is that Package Control will automatically keep SublimeBookmarks up to date with the latest version.



**Without Git:** Download the latest source from `GitHub <https://github.com/bollu/SublimeBookmark/tree/st3>` and copy the whole directory into the Packages directory.

**With Git:** Clone the repository in your Sublime Text Packages directory, located somewhere in user's "Home" directory::

	git clone -b st3 https://github.com/bollu/sublimeBookmark.git

To Use
======

###Adding Bookmarks###

Go to a line you wish to bookmark. Press ```ctrl + shift + P``` on Windows / Linux or ```cmd + shift + P``` on Mac and type ```SublimeBookmarks:Add Bookmark```. This opens up a panel where you can type the name of your bookmark. Once you're done naming your shiny new bookmark, hit ```Enter```. You should see a tiny yellow triangle next to your line. you're done!


###Accessing Bookmarks###
Press ```ctrl + shift + P```  on Windows / Linux or ```cmd + shift + P``` on Mac and select ```SublimeBookmarks:Goto Bookmark```. This will bring up a list of all bookmarks. Type in the bookmark name you want to go to and press ```Enter``` to go to the bookmark 


###Removing Bookmarks###
Press ```ctrl + shift + P```  on Windows / Linux or ```cmd + shift + P``` on Mac and select ```Remove Bookmark```. Type the name of the bookmark you want to remove and press ```Enter```. This will remove the bookmark

To remove _all_ bookmarks, select the option ```SublimeBookmarks:Remove All Bookmarks (Clear Bookmarks)```. This will clear _all bookmarks_. This _can not be undone_.  



##Projects:##

SublimeBookmarks tries to be smart and by default, only shows bookmarks that belong to the current project. So, if a bookmark is created when you are in a certain project, this bookmark will be visible __only when you are viewing that particular project__.


###Viewing all Bookmarks###

To view all bookmarks - not just bookmarks that belong to the project you are working on:

 Press ```ctrl + shift + P```  on Windows / Linux or ```cmd + shift + P``` on Mac and select ```SublimeBookmarks:Show All Bookmarks```

 This will show __all__ bookmarks created


###Viewing only Project Bookmarks###

To view bookmarks that only belong to the current project:

 Press ```ctrl + shift + P```  on Windows / Linux or ```cmd + shift + P``` on Mac and select ```SublimeBookmarks:Show Only Project Bookmarks```

This will only show bookmarks that belong to the current project.

Notes / Addendum
================

###Some TODO Stuff:###

* Port to Sublime Text 2
* <del>Add an option to only show bookmarks belonging to current project </del>   (Nope, it now fully supports project-based bookmark management!)


###To Help###

Just fork my repo and send a pull request. I'll gladly accept :)


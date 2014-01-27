SublimeBookmark
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

**Note**: <del> As of now, This is only for **Sublime Text 3**. </del> False! It's been ported. Unfortunately, I havent' implement live preview and project based bookmark sorting. I'm not sure how to port these features over to Sublime Text 2. If someone knows, please do contact me!


Features
========

* Named bookmarks
* Bookmarks are saved across sessions
* Goto any bookmark in the project
* Add any number of bookmarks (not just 12).
* Project based bookmarks (bookmarks are stored per-project and bookmarks can be navigated on a per-project basis) (Only for ST3)

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



##Visibility Modes:##

SublimeBookmarks has 3 visibility modes associated with it:


###1) View all Bookmarks###

 This mode shows *all* bookmarks that have been created - irrespective of project or file information.


 To use this mode, Press ```ctrl + shift + P```  on Windows / Linux or ```cmd + shift + P``` on Mac and select ```SublimeBookmarks:Show All Bookmarks```

 This will show __all__ bookmarks created


###2) View only Project Bookmarks###

 This mode only shows bookmarksthat belong to the *current project* - it will not show other bookmarks *at all*

 Press ```ctrl + shift + P```  on Windows / Linux or ```cmd + shift + P``` on Mac and select ```SublimeBookmarks:Show Only Bookmarks In Current Project```

This will only show bookmarks that belong to the current project.

###2) View only current file Bookmarks###

 This mode only shows bookmark that are present in the *current file*.

 Press ```ctrl + shift + P```  on Windows / Linux or ```cmd + shift + P``` on Mac and select ```SublimeBookmarks:Show Only Bookmarks In Current File```

This will only show bookmarks that belong to the current project.

Notes / Addendum
================

###Some TODO Stuff:###

* <del>Port to Sublime Text 2 </del> (This is partially done. Unfortunately, I'm not able to implement live previews and project support. I don't really know how to port these to ST2. If someone does, please do contact me! )
* <del>Add an option to only show bookmarks belonging to current project </del>   (Nope, it now fully supports project-based bookmark management!)


###To Help###

Just fork my repo and send a pull request. I'll gladly accept :)

I've spent quite some time writing this and making it bug-free. It would really help me if you'd chip in a little something :) I'm a student, so a little goes a long way.

[![Support via Gittip](https://rawgithub.com/twolfson/gittip-badge/0.1.0/dist/gittip.png)](https://www.gittip.com/bollu/)


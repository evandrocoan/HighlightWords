HighlightWords
==============

A Sublime Text 2 and 3 plugin for highlighting mutiple words in different colors

The following configuration options are available:
* Regular Expression
* Case Sensitive
* Customize Highlight Colors
* Define "Always Highlighted Keywords" with Customized Colors


## Installation

### By Package Control

1. Download & Install **`Sublime Text 3`** (https://www.sublimetext.com/3)
1. Go to the menu **`Tools -> Install Package Control`**, then,
   wait few seconds until the installation finishes up
1. Now,
   Go to the menu **`Preferences -> Package Control`**
1. Type **`Add Channel`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
   input the following address and press <kbd>Enter</kbd>
   ```
   https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json
   ```
1. Go to the menu **`Tools -> Command Palette...
   (Ctrl+Shift+P)`**
1. Type **`Preferences:
   Package Control Settings – User`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
   find the following setting on your **`Package Control.sublime-settings`** file:
   ```js
       "channels":
       [
           "https://packagecontrol.io/channel_v3.json",
           "https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json",
       ],
   ```
1. And,
   change it to the following, i.e.,
   put the **`https://raw.githubusercontent...`** line as first:
   ```js
       "channels":
       [
           "https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json",
           "https://packagecontrol.io/channel_v3.json",
       ],
   ```
   * The **`https://raw.githubusercontent...`** line must to be added before the **`https://packagecontrol.io...`** one, otherwise,
     you will not install this forked version of the package,
     but the original available on the Package Control default channel **`https://packagecontrol.io...`**
1. Now,
   go to the menu **`Preferences -> Package Control`**
1. Type **`Install Package`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
search for **`HighlightWords`** and press <kbd>Enter</kbd>

See also:

1. [ITE - Integrated Toolset Environment](https://github.com/evandrocoan/ITE)
1. [Package control docs](https://packagecontrol.io/docs/usage) for details.


Usage
------------------
* Highlight: Select "Edit > Highlight Words > Highlight Words" and enter the words (separated by whitespace)
* Unhighlight: Select "Edit > Highlight Words > Unhighlight Words"
* Toggle Settings: Select "Edit > Highlight Words > Toggle Settings"
* Edit settings file: Select "Preferences" > "Package Settings" > "HighlightWords", copy settings from default to user, and edit settings file. Available settings are:
 - "colors_by_scope": Change the highlight colors.
 - "permanent_highlight_keyword_color_mappings": Define always highlighted keywords with specified colors, such as "TODO" or "FIXIT". The optional "flag" parameter may be 0 (regex), 1 (literal), 2 (regex and ignore case) or 3 (literal and ignore case).
* Perl-style regular expression patterns are accepted.
  For example,
  to highlight "fix a bug" but not "prefix with",
  the expression could be "\\bfix .\*\\b".
* You can create a regex search targeting the words you want to match with `/regex/`.
  For example,
  if you enter `/(?: => )([^\s]+)/ word1` on the panel,
  it will highlight all the words matched by the regex `([^\s]+)` plus the `word1`.

Note: These commands are also available in Command Panel with prefix "**HighlightWords:**"

How to find color scope
------------------
  * Open the file that has some color you want (e.g open C++ which have green strings)
  * Select the word that has colour you want to use

  ![selection](doc_images/selection.png)
  * Open console (ctrl+~ (tilde))
  * Paste `view.scope_name(view.sel()[0].begin())` and press `ENTER`
  * Copy returned string, for mine selection it is `source.c++ meta.function.c meta.block.c storage.type.c`
  * Paste this string inside color property:

  ![highlight](doc_images/highlight.png)

  **Color will change after you re-enter the tab**


Contact me
------------------
Please visit me if you have any question or suggestion at: http://weibo.com/seanliang

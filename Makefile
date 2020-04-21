
LIVE_VERSION = 10.1.9

PATH_TO_ABLETON_APP = /Applications/Ableton\ Live\ 10\ Intro.app/Contents/App-Resources/MIDI\ Remote\ Scripts
PATH_TO_ABLETON_LOG_FILE = /Users/$(shell whoami)/Library/Preferences/Ableton/Live\ $(LIVE_VERSION)/Log.txt
ABLETON_SURFACE_NAME = AAAOP_1_Custom

.PHONY: install
install: uninstall
	ln -s `pwd` $(PATH_TO_ABLETON_APP)/$(ABLETON_SURFACE_NAME)


.PHONY: uninstall
uninstall:
	rm -f $(PATH_TO_ABLETON_APP)/$(ABLETON_SURFACE_NAME)


.PHONY: clean
clean:
	rm *.pyc


.PHONY: log
log:
	tail -f $(PATH_TO_ABLETON_LOG_FILE) | grep -E "(RemoteScriptError|RemoteScriptMessage): "

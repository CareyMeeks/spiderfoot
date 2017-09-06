# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         sfp_citadel
# Purpose:      SpiderFoot plug-in to search citadel.pw using their API, for
#               potential data breaches.
#
# Author:      sn <citadel.pw@protonmail.com>
#
# Created:     15/08/2017
# Licence:     GPL
# -------------------------------------------------------------------------------

import json
from sflib import SpiderFoot, SpiderFootPlugin, SpiderFootEvent

class sfp_citadel(SpiderFootPlugin):
    """Citadel Engine:Footprint,Investigate,Passive:Databases:apikey:Searches citadel.pw's database of breaches."""

    # Default options
    opts = {
        "api_key": "",
	"timeout": 60
    }
    optdescs = {
	"api_key": "citadel.pw API key. Without this you're limited to the public API.",
	"timeout": "Custom timeout due to heavy traffic at times."
    }

    results = dict()
    errorState = False

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        self.results = dict()

        for opt in userOpts.keys():
            self.opts[opt] = userOpts[opt]

    # What events is this module interested in for input
    def watchedEvents(self):
        return ['EMAILADDR']

    # What events this module produces
    # This is to support the end user in selecting modules based on events
    # produced.
    def producedEvents(self):
        return ["EMAILADDR_COMPROMISED"]

    # Handle events sent to this module
    def handleEvent(self, event):
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data

        try:
            if self.errorState:
                    return None

            self.sf.debug("Received event, " + eventName + ", from " + srcModuleName)

            if self.opts['api_key'] == "":
                    self.sf.info("You enabled sfp_citadel but did not set an API key!")
                    self.errorState = False

            # Don't look up stuff twice
            if eventData in self.results:
                    self.sf.debug("Skipping " + eventData + " as already searched.")
                    return None
            else:
                    self.results[eventData] = True

            if self.opts['api_key']:
                    url = "http://citadel.pw/api.php?api=" + self.opts['api_key'] + "&query="
            else:
                    url = "http://citadel.pw/api.php?api=6ce4f0a0c7b776809adb0f90473ea0e4&query="

	    res = self.sf.fetchUrl(url + eventData, timeout=self.opts['timeout'], useragent=self.opts['_useragent'])

            if res['content'] is None or "{error" in res['content']:
                self.sf.error("Error encountered processing " + eventData, False)
                return None

            data = json.loads(res['content'])

            if "error" in data[0]:
                self.sf.error("Error encountered processing. Error:" + data[0]['error'], False)
                return None

            if "site" in data[0]:
                for record in data:
                    self.sf.info("Found Citadel entry for " + eventData + ": " + record["site"])
                    t = "EMAILADDR_COMPROMISED"
                    evt = SpiderFootEvent(t, record["site"], self.__name__, event)
                    self.notifyListeners(evt)
                return None

        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print message

# End of sfp_citadel class


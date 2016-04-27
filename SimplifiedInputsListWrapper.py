__author__ = 'Wouter'

import urllib2
import json
import urllib

class SIL():
    def __init__(self, url):
        self.url = url


    def get(self, address, height=0):
        parameters = {}
        parameters['format'] = 'json'
        parameters['address'] = address

        SIL = []

        if height != 0:
            parameters['block'] = str(height)

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/SIL?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve SIL")

        if 'success' in data and data['success'] == 1:
            SIL = data['SIL']

        return SIL
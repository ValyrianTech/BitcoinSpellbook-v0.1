__author__ = 'Wouter'
import urllib2
import json
import urllib


class Blocklinker():
    def __init__(self, url):
        self.url = url


    def get(self, address, xpub, height=0, metric='LAL'):
        parameters = {}
        parameters['format'] = 'json'
        parameters['address'] = address
        parameters['xpub'] = xpub
        parameters['metric'] = metric

        result = []

        if height != 0:
            parameters['block'] = str(height)

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/LinkedList?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve " + metric)

        if 'success' in data and data['success'] == 1:
            result = data[metric]

        return result
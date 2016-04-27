__author__ = 'Wouter'
import urllib2
import json
import urllib


class ProportionalRandom():
    def __init__(self, url):
        self.url = url


    def randomAddress(self, address, block=0, metric='SIL', regBlock=0 , xpub=''):
        parameters = {}
        parameters['format'] = 'json'
        parameters['address'] = address
        parameters['metric'] = metric

        result = []

        if xpub != '':
            parameters['xpub'] = xpub

        if block != 0:
            parameters['block'] = str(block)

        if regBlock != 0:
            parameters['regBlock'] = str(regBlock)

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/ProportionalRandom?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve " + metric)

        if 'success' in data and data['success'] == 1:
            result = data['winner']['winnerAddress']

        return result

    def winner(self, address, block=0, metric='SIL', regBlock=0, xpub=''):
        parameters = {}
        parameters['format'] = 'json'
        parameters['address'] = address
        parameters['metric'] = metric

        result = []

        if xpub != '':
            parameters['xpub'] = xpub

        if block != 0:
            parameters['block'] = str(block)

        if regBlock != 0:
            parameters['regBlock'] = str(regBlock)

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/ProportionalRandom?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve " + metric)

        if 'success' in data and data['success'] == 1:
            result = data['winner']

        return result
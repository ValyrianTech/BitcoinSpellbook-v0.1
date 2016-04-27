__author__ = 'Wouter'
import urllib2
import json
import urllib


class Bitvoter():
    def __init__(self, url):
        self.url = url

    def proposal(self, proposalAddress, proposal="", options=[], digits=1, weights='Value', registrationAddress="", registrationHeight=0, registrationXpub="", cost=50000):
        parameters = {}
        parameters['format'] = 'json'
        parameters['address'] = proposalAddress
        parameters['digits'] = str(digits)
        parameters['weights'] = weights
        parameters['cost'] = str(cost)

        result = []

        if proposal != "":
            parameters['proposal'] = str(proposal)

        if options != []:
            strOptions = ""
            for option in options:
                strOptions += option + "|"

            strOptions = strOptions[:-1]
            parameters['options'] = strOptions


        if registrationAddress != "":
            parameters['regAddress'] = str(registrationAddress)

        if registrationHeight != 0:
            parameters['regBlock'] = str(registrationHeight)

        if registrationXpub != "":
            parameters['regXPUB'] = str(registrationXpub)


        queryString  = urllib.urlencode(parameters)
        url = self.url +"/proposal?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve data")

        if 'success' in data and data['success'] == 1:
            result = data['proposal']

        return result


    def results(self, proposalAddress, proposalHeight=0, digits=1, weights='Value', registrationAddress="", registrationHeight=0, registrationXpub=""):
        result = []
        parameters = {}
        parameters['format'] = 'json'
        parameters['proposalAddress'] = proposalAddress
        parameters['digits'] = str(digits)
        parameters['weights'] = weights

        url = self.url + "/results?format=json&proposalAddress=" + proposalAddress + "&digits=" + str(digits) + "&weights=" + weights

        if proposalHeight != 0:
            parameters['proposalBlock'] = str(proposalHeight)

        if registrationAddress != "":
            parameters['regAddress'] = str(registrationAddress)

        if registrationHeight != 0:
            parameters['regBlock'] = str(registrationHeight)

        if registrationXpub != "":
            parameters['regXPUB'] = str(registrationXpub)

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/results?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve data")

        if 'success' in data and data['success'] == 1:
            result = data['results']

        return result
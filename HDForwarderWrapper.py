#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import json
import urllib
import hashlib
import hmac
import base64


class HDForwarder():
    def __init__(self, url):
        self.url = url

    def getForwarders(self):
        parameters = {}
        parameters['format'] = 'json'

        result = {}

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/?" + queryString


        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve forwarders")

        if 'success' in data and data['success'] == 1:
            result = data['forwarders']

        return result


    def forwarder(self, forwarderID):
        parameters = {}
        parameters['format'] = 'json'
        parameters['forwarderID'] = str(forwarderID)

        result = {}

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve forwarder information")

        if 'success' in data and data['success'] == 1:
            result = data['forwarder']

        return result


    def newForwarder(self, name, xpub, APIkey='', APIsecret=''):
        parameters ={}
        parameters['ID'] = 0
        parameters['Name'] = name
        parameters['XPUB'] = xpub
        url = self.url + "/updateForwarder?"

        postdata = urllib.urlencode(parameters)
        message = hashlib.sha256(postdata).digest()
        signature = hmac.new(base64.b64decode(APIsecret), message, hashlib.sha512)

        headers = {
            'API-Key': APIkey,
            'API-Sign': base64.b64encode(signature.digest())
        }

        try:
            request = urllib2.Request(url=url, data=postdata, headers=headers)
            response = urllib2.urlopen(request).read()
            data = json.loads(response)
        except:
            raise Exception("Unable to create new forwarder")

        result = {}
        if 'success' in data and data['success'] == 1:
            result = data['forwarder']
        elif 'error' in data:
            result = data['error']

        return result


    def updateForwarder(self, parameters={}, APIkey='', APIsecret=''):
        url = self.url +"/updateForwarder?"

        postdata = urllib.urlencode(parameters)
        message = hashlib.sha256(postdata).digest()
        signature = hmac.new(base64.b64decode(APIsecret), message, hashlib.sha512)

        headers = {
            'API-Key': APIkey,
            'API-Sign': base64.b64encode(signature.digest())
        }


        try:
            request = urllib2.Request(url=url, data=postdata, headers=headers)
            response = urllib2.urlopen(request).read()
            data = json.loads(response)
        except:
            raise Exception("Unable to update forwarder")

        result = {}
        if 'success' in data and data['success'] == 1:
            result = data['forwarder']
        elif 'error' in data:
            result = data['error']

        return result


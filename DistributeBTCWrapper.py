#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import json
import urllib
import hashlib
import hmac
import base64

class DistributeBTC():
    def __init__(self, url):
        self.url = url

    def getDistributers(self):
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
            raise Exception("Unable to retrieve distributers")

        if 'success' in data and data['success'] == 1:
            result = data['distributers']

        return result


    def distributer(self, distributerID):
        parameters = {}
        parameters['format'] = 'json'
        parameters['distributerID'] = str(distributerID)

        result = {}

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve distributer information")

        if 'success' in data and data['success'] == 1:
            result = data['distributer']

        return result

    def newDistributer(self, name, APIkey='', APIsecret=''):
        parameters ={}
        parameters['ID'] = 0
        parameters['Name'] = name

        url = self.url + "/updateDistributer?"

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
            raise Exception("Unable to create new distributer")

        result = {}
        if 'success' in data and data['success'] == 1:
            result = data['distributer']
        elif 'error' in data:
            result = data['error']

        return result

    def updateDistributer(self, parameters={}, APIkey='', APIsecret=''):
        url = self.url +"/updateDistributer?"

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
            raise Exception("Unable to update distributer")

        result = {}
        if 'success' in data and data['success'] == 1:
            result = data['distributer']
        elif 'error' in data:
            result = data['error']

        return result


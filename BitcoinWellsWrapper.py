#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import json
import urllib
import hashlib
import hmac
import base64

class BitcoinWells():
    def __init__(self, url):
        self.url = url

    def getWells(self):
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
            raise Exception("Unable to retrieve wells")

        if 'success' in data and data['success'] == 1:
            result = data['wells']

        return result


    def well(self, wellID):
        parameters = {}
        parameters['format'] = 'json'
        parameters['wellID'] = str(wellID)

        result = {}

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve well information")

        if 'success' in data and data['success'] == 1:
            result = data['well']

        return result

    def newWell(self, name, address, APIkey='', APIsecret=''):
        parameters ={}
        parameters['ID'] = 0
        parameters['Name'] = name
        parameters['Address'] = address

        url = self.url + "/updateWell?"

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
            raise Exception("Unable to create new well")

        result = {}
        if 'success' in data and data['success'] == 1:
            result = data['well']
        elif 'error' in data:
            result = data['error']

        return result

    def updateWell(self, parameters={}, APIkey='', APIsecret=''):
        url = self.url +"/updateWell?"

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
            raise Exception("Unable to update well")

        result = {}
        if 'success' in data and data['success'] == 1:
            result = data['well']
        elif 'error' in data:
            result = data['error']

        return result

    def newCampaign(self, name, wellID, targetAmount, APIkey='', APIsecret=''):
        parameters ={}
        parameters['ID'] = 0
        parameters['WellID'] = wellID
        parameters['Name'] = name
        parameters['TargetAmount'] = targetAmount

        url = self.url + "/updateCampaign?"

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
            raise Exception("Unable to create new campaign")

        result = {}
        if 'success' in data and data['success'] == 1:
            result = data['campaign']
        elif 'error' in data:
            result = data['error']

        return result


    def updateCampaign(self, parameters={}, APIkey='', APIsecret=''):
        url = self.url +"/updateCampaign?"

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
            raise Exception("Unable to update campaign")

        result = {}
        if 'success' in data and data['success'] == 1:
            result = data['campaign']
        elif 'error' in data:
            result = data['error']

        return result


    def newMilestone(self, name, wellID, campaingID, percent, APIkey='', APIsecret=''):
        parameters ={}
        parameters['ID'] = 0
        parameters['WellID'] = wellID
        parameters['CampaignID'] = campaingID
        parameters['Name'] = name
        parameters['Percent'] = percent

        url = self.url + "/updateMilestone?"

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
            raise Exception("Unable to create new milestone")

        result = {}
        if 'success' in data and data['success'] == 1:
            result = data['milestone']
        elif 'error' in data:
            result = data['error']

        return result


    def updateMilestone(self, parameters={}, APIkey='', APIsecret=''):
        url = self.url +"/updateMilestone?"

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
            raise Exception("Unable to update milestone")

        result = {}
        if 'success' in data and data['success'] == 1:
            result = data['milestone']
        elif 'error' in data:
            result = data['error']

        return result

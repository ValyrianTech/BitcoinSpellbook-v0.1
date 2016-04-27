#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import urllib2
import json
import hashlib
import hmac
import base64
import logging
import jinja2
import webapp2
import BIP44Tools
from google.appengine.api import users
from google.appengine.ext import ndb
import time
import re
import bitcoin
import includes

from google.appengine.api import urlfetch
urlfetch.set_default_fetch_deadline(60)

SOCIALBUTTONS_ENABLED = False
REQUIRED_CONFIRMATIONS = 3 #must be at least 3
TRANSACTION_FEE = 10000 #in Satoshis

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

#Default URLs for Bitcoin Spellbook modules
BLOCKCHAINDATA_URL = "https://blockchaindata.appspot.com"
SIMPLIFIEDINPUTSLIST_URL = "https://simplifiedinputslist.appspot.com"
BLOCKLINKER_URL = "https://blocklinker.appspot.com"
PROPORTIONALRANDOM_URL = "https://proportionalrandom.appspot.com"
BITVOTER_URL = "https://bitvoter.appspot.com"
HDFORWARDER_URL = "https://hdforwarder.appspot.com"
DISTRIBUTEBTC_URL = "https://distributebtc.appspot.com"
BITCOINWELLS_URL = "https://bitcoinwells.appspot.com"

def Spellbook(parameters):
    spellbook_urls = []

    spellbook_urls.append({'url': parameters.blockchaindataURL, 'name': 'Blockchaindata'})
    spellbook_urls.append({'url': parameters.simplifiedInputsListURL, 'name': 'Simplified Inputs List'})
    spellbook_urls.append({'url': parameters.blocklinkerURL, 'name': 'Blocklinker'})
    spellbook_urls.append({'url': parameters.bitvoterURL, 'name': 'Bitvoter'})
    spellbook_urls.append({'url': parameters.proportionalRandomURL, 'name': 'Proportional Random'})
    spellbook_urls.append({'url': parameters.hdforwarderURL, 'name': 'HDForwarder'})
    spellbook_urls.append({'url': parameters.distributeBTCURL, 'name': 'DistributeBTC'})
    spellbook_urls.append({'url': parameters.bitcoinWellsURL, 'name': 'BitcoinWells'})

    return spellbook_urls



class Parameters(ndb.Model):
    #Model for parameters
    trackingID = ndb.StringProperty(indexed=False, default="")
    blockchaindataURL = ndb.StringProperty(indexed=False, default=BLOCKCHAINDATA_URL)
    simplifiedInputsListURL = ndb.StringProperty(indexed=False, default=SIMPLIFIEDINPUTSLIST_URL)
    blocklinkerURL = ndb.StringProperty(indexed=False, default=BLOCKLINKER_URL)
    proportionalRandomURL = ndb.StringProperty(indexed=False, default=PROPORTIONALRANDOM_URL)
    bitvoterURL = ndb.StringProperty(indexed=False, default=BITVOTER_URL)
    hdforwarderURL = ndb.StringProperty(indexed=False, default=HDFORWARDER_URL)
    distributeBTCURL = ndb.StringProperty(indexed=False, default=DISTRIBUTEBTC_URL)
    bitcoinWellsURL = ndb.StringProperty(indexed=False, default=BITCOINWELLS_URL)
    walletseed = ndb.StringProperty(indexed=False, default="")
    APIkey = ndb.StringProperty(indexed=False, default="")
    APIsecret = ndb.StringProperty(indexed=False, default="") #must be a multiple of 4 characters!!!


def distributers_key():
    #Constructs a Datastore key for a Distributer entity
    return ndb.Key('DistributeBTC', 'DistributeBTC')

def getNextIndex():
    i = 0
    distributers_query = Distributer.query(ancestor=distributers_key()).order(-Distributer.walletIndex)
    distributers = distributers_query.fetch()

    if len(distributers) > 0:
        i = distributers[0].walletIndex + 1

    return i

def validEmail(email):
    valid = False
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        valid = True

    return valid


def validXPUB(xpub):
    valid =False
    if xpub[:4] == "xpub":
        valid = True

    return valid

def validDistribution(distribution):
    valid = False

    if isinstance(distribution, list):
        if len(distribution) >= 1:
            for recipient in distribution:
                if not isinstance(recipient, list):
                    valid = False
                    break
                elif len(recipient) != 2:
                    valid = False
                    break
                elif not isinstance(recipient[0], unicode):
                    valid = False
                    break
                elif not isinstance(recipient[1], int):
                    valid = False
                    break
                elif recipient[1] <= 0:
                    valid = False
                    break
                else:
                    valid = True

    return valid




class Distributer(ndb.Model):
    userID = ndb.StringProperty('u', indexed=True)
    addressType = ndb.StringProperty('t', choices=['BIP44', 'PrivKey'], default='BIP44')
    walletIndex = ndb.IntegerProperty('i', indexed=True, default=0)
    privateKey = ndb.StringProperty('p', indexed=False, default='')
    creator = ndb.StringProperty('c', default='')
    creatorEmail = ndb.StringProperty('e', default='')
    name = ndb.StringProperty('n', indexed=True)
    address = ndb.StringProperty('a', indexed=True)
    distributionSource = ndb.StringProperty('ds', choices=['Custom', 'SIL', 'LBL', 'LRL', 'LSL'], default='Custom')
    custom = ndb.TextProperty('cd', default='[]')
    registrationAddress = ndb.StringProperty('ra', default='')
    registrationXPUB = ndb.StringProperty('rx', default= '')
    registrationBlockheight = ndb.IntegerProperty('rb', default=0)
    threshold = ndb.IntegerProperty('th', default=0)
    minimumAmount = ndb.IntegerProperty('m', default=0)
    date = ndb.DateTimeProperty('dt', auto_now_add=True)
    description = ndb.TextProperty('d', default='')
    youtube = ndb.StringProperty('y', default='')
    status = ndb.StringProperty('s', choices=['Pending', 'Active', 'Disabled'], default='Pending')
    visibility = ndb.StringProperty('v', choices=['Public', 'Private'], default='Private')
    transactionFee = ndb.IntegerProperty('tf', default=TRANSACTION_FEE)
    feePercent = ndb.FloatProperty('fp', default=0.0)
    feeAddress = ndb.StringProperty('fa', default='')







class MainPage(webapp2.RequestHandler):

    def get(self):
        distribution = []
        distributerID = 0
        beneficiaryAddress = ''
        beneficiaryBalance = 0
        beneficiaryShare = 0

        showWarning = True

        parameters = Parameters.get_or_insert('DefaultConfig')

        if self.request.get('distributerID'):
            distributerID = int(self.request.get('distributerID'))
            distributers = [Distributer.get_by_id(distributerID, parent=distributers_key())]


            if distributers[0].distributionSource == 'Custom':
                distribution = json.loads(distributers[0].custom)
            else:
                if distributers[0].distributionSource in ['LBL', 'LRL', 'LSL']:
                    url = parameters.blocklinkerURL + '/LinkedList?format=json&address=' + distributers[0].registrationAddress + '&xpub=' + distributers[0].registrationXPUB + '&block=' + str(distributers[0].registrationBlockheight) + '&metric=LAL,' + distributers[0].distributionSource
                elif distributers[0].distributionSource == 'SIL':
                    url = parameters.simplifiedInputsListURL + '/SIL?format=json&address=' + distributers[0].registrationAddress + '&block=' + str(distributers[0].registrationBlockheight)

                data = {}
                try:
                    ret = urllib2.urlopen(urllib2.Request(url))
                    data = json.loads(ret.read())
                except:
                    data = {}

                if 'success' in data and data['success'] == 1:
                    if 'SIL' in data:
                        distribution = data['SIL']
                    elif 'LBL' in data:
                        distribution = data['LBL']
                    elif 'LRL' in data:
                        distribution = data['LRL']
                    elif 'LSL' in data:
                        distribution = data['LSL']


            if self.request.get('address'):
                address = self.request.get('address')

                totalShares = 0
                beneficiaryValue = 0
                for i in range(0, len(distribution)):
                    totalShares += distribution[i][1]
                    if distribution[i][0] == address:
                        beneficiaryAddress = address
                        beneficiaryValue = distribution[i][1]
                        showWarning = False


                if totalShares > 0:
                    beneficiaryShare = beneficiaryValue/float(totalShares)*100


            else:
                showWarning = False

        else:
            showWarning = False
            distributers_query = Distributer.query(Distributer.visibility == 'Public', Distributer.status == 'Active').order(-Distributer.date)
            distributers = distributers_query.fetch()

        isAdmin = False
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'


        if self.request.get('distributerID') and self.request.get('format') == 'json':
            response = {'success': 1, 'distributer': []}
            if len(distributers) == 1:
                distributer = distributers[0]
                tmpDistributer = {}
                tmpDistributer['ID'] = distributer.key.id()
                tmpDistributer['Name'] = distributer.name
                tmpDistributer['Address'] = distributer.address
                tmpDistributer['Description'] = distributer.description
                tmpDistributer['Creator'] = distributer.creator
                tmpDistributer['CreatorEmail'] = distributer.creatorEmail
                tmpDistributer['Youtube'] = distributer.youtube
                tmpDistributer['Status'] = distributer.status
                tmpDistributer['FeeAddress'] = distributer.feeAddress
                tmpDistributer['FeePercent'] = distributer.feePercent
                tmpDistributer['Custom'] = distributer.custom
                tmpDistributer['DistributionSource'] = distributer.distributionSource
                tmpDistributer['Threshold'] = distributer.threshold
                tmpDistributer['MinimumAmount'] = distributer.minimumAmount
                tmpDistributer['TransactionFee'] = distributer.transactionFee
                tmpDistributer['RegistrationAddress'] = distributer.registrationAddress
                tmpDistributer['RegistrationBlockheight'] = distributer.registrationBlockheight
                tmpDistributer['RegistrationXPUB'] = distributer.registrationXPUB
                tmpDistributer['Visibility'] = distributer.visibility
                tmpDistributer['Date'] = int(time.mktime(distributer.date.timetuple()))
                response['distributer'] = tmpDistributer


            self.response.write(json.dumps(response))

        elif not self.request.get('distributerID') and self.request.get('format') == 'json':
            response = {'success': 1, 'distributers': []}
            for distributer in distributers:
                tmpDistributer = {}
                tmpDistributer['ID'] = distributer.key.id()
                tmpDistributer['Name'] = distributer.name
                tmpDistributer['Address'] = distributer.address
                tmpDistributer['Description'] = distributer.description
                tmpDistributer['Creator'] = distributer.creator
                tmpDistributer['CreatorEmail'] = distributer.creatorEmail
                tmpDistributer['Youtube'] = distributer.youtube
                tmpDistributer['Status'] = distributer.status
                tmpDistributer['FeeAddress'] = distributer.feeAddress
                tmpDistributer['FeePercent'] = distributer.feePercent
                tmpDistributer['Custom'] = distributer.custom
                tmpDistributer['DistributionSource'] = distributer.distributionSource
                tmpDistributer['Threshold'] = distributer.threshold
                tmpDistributer['MinimumAmount'] = distributer.minimumAmount
                tmpDistributer['TransactionFee'] = distributer.transactionFee
                tmpDistributer['RegistrationAddress'] = distributer.registrationAddress
                tmpDistributer['RegistrationBlockheight'] = distributer.registrationBlockheight
                tmpDistributer['RegistrationXPUB'] = distributer.registrationXPUB
                tmpDistributer['Visibility'] = distributer.visibility
                tmpDistributer['Date'] = int(time.mktime(distributer.date.timetuple()))
                response['distributers'].append(tmpDistributer)


            self.response.write(json.dumps(response))

        else:
            template_values = {
                'url': url,
                'url_linktext': url_linktext,

                'distributers': distributers,
                'distributerID': distributerID,
                'distribution': distribution,
                'nDistribution': len(distribution),

                'showWarning': showWarning,

                'beneficiaryAddress': beneficiaryAddress,
                'beneficiaryBalance' : beneficiaryBalance,
                'beneficiaryShare': '%.2f' % beneficiaryShare,


                'cssHTML': includes.get_CssHTML(),
                'metaHTML': includes.get_MetaHTML(),
                'scriptsHTML': includes.get_ScriptsHTML(),
                'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
                'logoHTML': includes.get_LogoHTML(),
                'footerHTML': includes.get_FooterHTML(),
                'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),

                'socialButtons': SOCIALBUTTONS_ENABLED,


            }


            template = JINJA_ENVIRONMENT.get_template('index.html')

            self.response.write(template.render(template_values))



class EditDistributer(webapp2.RequestHandler):

    def get(self):
        isAdmin = False
        error = ''
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        distributerID = 0
        distributer = Distributer(parent=distributers_key())
        if self.request.get('distributerID'):
            try:
                distributerID = int(self.request.get('distributerID'))
                distributer = Distributer.get_by_id(distributerID, parent=distributers_key())
            except ValueError:
                error = 'distributerID must be a integer'




        parameters = Parameters.get_or_insert('DefaultConfig')
        template_values = {
            'distributer': distributer,
            'distributerID': distributerID,

            'url': url,
            'url_linktext': url_linktext,
            'cssHTML': includes.get_CssHTML(),
            'metaHTML': includes.get_MetaHTML(),
            'scriptsHTML': includes.get_ScriptsHTML(),
            'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
            'logoHTML': includes.get_LogoHTML(),
            'footerHTML': includes.get_FooterHTML(),
            'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
        }

        template = JINJA_ENVIRONMENT.get_template('editDistributer.html')
        self.response.write(template.render(template_values))


class SaveDistributer(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def post(self):

        distributerID = 0
        distributer = Distributer(parent=distributers_key())
        if self.request.get('DistributerID'):
            try:
                distributerID = int(self.request.get('DistributerID'))
                distributer = Distributer.get_by_id(distributerID, parent=distributers_key())
            except ValueError:
                error = 'DistributerID must be a integer'

            distributer.name = self.request.get('DistributerName')
            distributer.description = self.request.get('Description')
            distributer.creator = self.request.get('Creator')
            distributer.creatorEmail = self.request.get('CreatorEmail')


            distributer.walletIndex = int(self.request.get('WalletIndex'))
            distributer.privateKey = self.request.get('PrivateKey')
            distributer.addressType = self.request.get('AddressType')

            if self.request.get('DistributionSource') in ['Custom', 'SIL', 'LBL', 'LRL', 'LSL']:
                distributer.distributionSource = self.request.get('DistributionSource')

            distributer.custom = self.request.get('CustomDistribution')
            distributer.registrationAddress = self.request.get('RegistrationAddress')
            distributer.registrationXPUB = self.request.get('RegistrationXPUB')
            distributer.registrationBlockheight = int(self.request.get('RegistrationBlockheight'))

            distributer.threshold = int(self.request.get('Threshold'))
            distributer.minimumAmount = int(self.request.get('MinimumAmount'))
            distributer.transactionFee = int(self.request.get('TransactionFee'))
            distributer.youtube = self.request.get('Youtube')
            if self.request.get('Visibility') in ['Public', 'Private']:
                distributer.visibility = self.request.get('Visibility')

            if self.request.get('Status') in ['Pending', 'Active', 'Disabled']:
                distributer.status = self.request.get('Status')

            distributer.feePercent = float(self.request.get('FeePercent'))
            distributer.feeAddress = self.request.get('FeeAddress')


            distributer_key = distributer.put()
            self.redirect('/getAddress?id=' + str(distributer_key.id()))



class UpdateDistributer(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def post(self):
        error = ''
        distributerID = 0
        response = {'success': 0}

        parameters = Parameters.get_or_insert('DefaultConfig')

        if 'API-Key' in self.request.headers:
            APIkey = self.request.headers['API-Key']
            if APIkey != parameters.APIkey and parameters.APIkey != '':
                error = 'Incorrect APIkey'
                response = {'success': 0, 'error': error}
        else:
            error = 'No APIkey supplied'
            response = {'success': 0, 'error': error}


        if 'API-Sign' in self.request.headers:
            signature = str(self.request.headers['API-Sign'])
            postdata = self.request.body
            message = hashlib.sha256(postdata).digest()
            if signature != base64.b64encode(hmac.new(base64.b64decode(parameters.APIsecret), message, hashlib.sha512).digest()):
                error =  'Invalid signature'
                response = {'success': 0, 'error': error}
        else:
            error = 'No signature supplied'
            response = {'success': 0, 'error': error}


        if self.request.get('ID') and error == '':
            try:
                distributerID = int(self.request.get('ID'))
            except ValueError:
                error = 'ID must be an integer'
                response = {'success': 0, 'error': error}

            if error == '':
                distributer = Distributer(parent=distributers_key())
                if distributerID != 0:
                    distributer = Distributer.get_by_id(distributerID, parent=distributers_key())

                if self.request.get('Name'):
                    if len(self.request.get('Name')) > 0:
                        distributer.name = self.request.get('Name')
                    else:
                        error = 'Name cannot be empty'

                if self.request.get('Description'):
                    distributer.description = self.request.get('Description')

                if self.request.get('DistributionSource'):
                    if self.request.get('DistributionSource') in ['Custom', 'SIL', 'LBL', 'LRL', 'LSL']:
                        distributer.distributionSource = self.request.get('DistributionSource')
                    else:
                        error = 'DistributionSource must be Custom, SIL, LBL, LRL or LSL'

                if self.request.get('Custom'):
                    customDistribution = eval(self.request.get('Custom'))
                    if validDistribution(customDistribution) or customDistribution == []:
                        distributer.custom = self.request.get('Custom')
                    else:
                        error = 'Invalid Custom distribution: ' + str(customDistribution)

                if self.request.get('RegistrationAddress'):
                    distributer.registrationAddress = self.request.get('RegistrationAddress')

                if self.request.get('RegistrationBlockheight'):
                    amount = -1
                    try:
                        amount = int(self.request.get('RegistrationBlockheight'))
                    except ValueError:
                        error = 'RegistrationBlockheight must be a positive integer or equal to 0'

                    if amount >= 0:
                        distributer.registrationBlockheight = amount
                    else:
                        error = 'RegistrationBlockheight must be a positive integer or equal to 0'

                if self.request.get('RegistrationXPUB'):
                    if validXPUB(self.request.get('RegistrationXPUB')):
                        distributer.registrationXPUB = self.request.get('RegistrationXPUB')
                    else:
                        error = 'Invalid RegistrationXPUB key'


                if self.request.get('Creator'):
                    distributer.creator = self.request.get('Creator')

                if self.request.get('CreatorEmail'):
                    if validEmail(self.request.get('CreatorEmail')):
                        distributer.creatorEmail = self.request.get('CreatorEmail')
                    else:
                        error = 'Invalid email address'

                if self.request.get('MinimumAmount'):
                    amount = -1
                    try:
                        amount = int(self.request.get('MinimumAmount'))
                    except ValueError:
                        error = 'MinimumAmount must be a positive integer or equal to 0 (in Satoshis)'

                    if amount >= 0:
                        distributer.minimumAmount = amount
                    else:
                        error = 'MinimumAmount must be a positive integer or equal to 0 (in Satoshis)'

                if self.request.get('Threshold'):
                    amount = -1
                    try:
                        amount = int(self.request.get('Threshold'))
                    except ValueError:
                        error = 'Threshold must be a positive integer or equal to 0 (in Satoshis)'

                    if amount >= 0:
                        distributer.threshold = amount
                    else:
                        error = 'Threshold must be a positive integer or equal to 0 (in Satoshis)'

                if self.request.get('TransactionFee'):
                    amount = -1
                    try:
                        amount = int(self.request.get('TransactionFee'))
                    except ValueError:
                        error = 'TransactionFee must be a positive integer (in Satoshis)'

                    if amount > 0:
                        distributer.transactionFee = amount
                    else:
                        error = 'TransactionFee must be a positive integer (in Satoshis)'

                if self.request.get('Youtube'):
                    distributer.youtube = self.request.get('Youtube')

                if self.request.get('Visibility'):
                    if self.request.get('Visibility') in ['Public', 'Private']:
                        distributer.visibility = self.request.get('Visibility')
                    else:
                        error = 'Visibility must be Public or Private'

                if self.request.get('Status'):
                    if self.request.get('Status') in ['Pending', 'Active', 'Disabled']:
                        distributer.status = self.request.get('Status')
                    else:
                        error = 'Status must be Pending, Active or Disabled'

                if self.request.get('FeePercent'):
                    percentage = -1
                    try:
                        percentage = float(self.request.get('FeePercent'))
                    except ValueError:
                        error = 'Incorrect Fee percentage'

                    if percentage >= 0:
                        distributer.feePercent = percentage
                    else:
                        error = 'FeePercent must be greater than or equal to 0'

                if self.request.get('FeeAddress'):
                    distributer.feeAddress = self.request.get('FeeAddress')

                if self.request.get('ConfirmAmount'):
                    amount = -1
                    try:
                        amount = int(self.request.get('ConfirmAmount'))
                    except ValueError:
                        error = 'ConfirmAmount must be a positive integer or equal to 0 (in Satoshis)'

                    if amount >= 0:
                        distributer.confirmAmount = amount
                    else:
                        error = 'ConfirmAmount must be greater than or equal to 0 (in Satoshis)'


                if self.request.get('AddressType'):
                    if self.request.get('AddressType') in ['PrivKey', 'BIP44']:
                        distributer.addressType = self.request.get('AddressType')
                    else:
                        error = 'AddressType must be BIP44 or PrivKey'

                if self.request.get('WalletIndex'):
                    index = -1
                    try:
                        index = int(self.request.get('WalletIndex'))
                    except ValueError:
                        error = 'WalletIndex must be a positive integer'

                    if index >= 0:
                        distributer.walletIndex = index
                    else:
                        error = 'Wallet index must be greater than or equal to 0'

                if self.request.get('PrivateKey'):
                    distributer.privateKey = self.request.get('PrivateKey')


                if error == '':
                    distributer.put()

                    if distributer.addressType == 'PrivKey' and distributer.privateKey != '':
                        newAddress = bitcoin.privtoaddr(distributer.privateKey)
                        if distributer.address != newAddress:
                            distributer.address = newAddress
                            distributer.put()
                    elif distributer.addressType == 'BIP44':
                        if parameters and (parameters.walletseed != None and parameters.walletseed != ""):
                            if distributer.walletIndex == 0:
                                distributer.walletIndex = getNextIndex()
                                #bugfix: when creating the first forwarder, set index to 1
                                if distributer.walletIndex == 0:
                                    distributer.walletIndex = 1
                                seed = parameters.walletseed
                                xpub = BIP44Tools.getTrezorXPUBKeys(seed)[0]
                                distributer.address = BIP44Tools.getAddressesFromXPUB(xpub, distributer.walletIndex + 1)[distributer.walletIndex]
                                distributer.put()


                    response['success'] = 1
                    tmpDistributer = {}
                    tmpDistributer['ID'] = distributer.key.id()
                    tmpDistributer['Name'] = distributer.name
                    tmpDistributer['Address'] = distributer.address
                    tmpDistributer['Description'] = distributer.description
                    tmpDistributer['Creator'] = distributer.creator
                    tmpDistributer['CreatorEmail'] = distributer.creatorEmail
                    tmpDistributer['Youtube'] = distributer.youtube
                    tmpDistributer['Status'] = distributer.status
                    tmpDistributer['FeeAddress'] = distributer.feeAddress
                    tmpDistributer['FeePercent'] = distributer.feePercent
                    tmpDistributer['Custom'] = distributer.custom
                    tmpDistributer['DistributionSource'] = distributer.distributionSource
                    tmpDistributer['Threshold'] = distributer.threshold
                    tmpDistributer['MinimumAmount'] = distributer.minimumAmount
                    tmpDistributer['TransactionFee'] = distributer.transactionFee
                    tmpDistributer['RegistrationAddress'] = distributer.registrationAddress
                    tmpDistributer['RegistrationBlockheight'] = distributer.registrationBlockheight
                    tmpDistributer['RegistrationXPUB'] = distributer.registrationXPUB
                    tmpDistributer['Visibility'] = distributer.visibility
                    tmpDistributer['Date'] = int(time.mktime(distributer.date.timetuple()))
                    response['distributer'] = tmpDistributer

                    self.response.write(json.dumps(response))
                else:
                    response['success'] = 0
                    response['error'] = error
                    self.response.write(json.dumps(response))

            else:
                self.response.write(json.dumps(response))

        else:
            self.response.write(json.dumps(response))





class AdminPage(webapp2.RequestHandler):

    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')
        distributerID = 0
        status = 'All'
        if self.request.get('status') in ['Pending', 'Active', 'Disabled']:
            status = self.request.get('status')

        if status != 'All':
            distributers_query = Distributer.query(Distributer.status == status).order(-Distributer.date)
        else:
            distributers_query = Distributer.query().order(-Distributer.date)

        if self.request.get('id'):
            distributerID = int(self.request.get('id'))
            distributers = [Distributer.get_by_id(distributerID, parent=distributers_key())]
        else:
            distributers = distributers_query.fetch()

        isAdmin = False
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

            
        template_values = {
            'distributers': distributers,
            'status': status,

            'cssHTML': includes.get_CssHTML(),
            'metaHTML': includes.get_MetaHTML(),
            'scriptsHTML': includes.get_ScriptsHTML(),
            'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
            'logoHTML': includes.get_LogoHTML(),
            'footerHTML': includes.get_FooterHTML(),
            'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
        }

        template = JINJA_ENVIRONMENT.get_template('admin.html')
        self.response.write(template.render(template_values))



class GetAddress(webapp2.RequestHandler):

    def get(self):
        if self.request.get('id'):
            id = int(self.request.get('id'))
            distributer = Distributer.get_by_id(id, parent=distributers_key())

            if distributer.addressType == 'PrivKey' and distributer.privateKey != '':
                distributer.address = bitcoin.privtoaddr(distributer.privateKey)
                distributer.put()


            elif distributer.addressType == 'BIP44':
                parameters = Parameters.get_or_insert('DefaultConfig')

                if parameters and (parameters.walletseed != None and parameters.walletseed != ""):
                    seed = parameters.walletseed
                    xpub = BIP44Tools.getTrezorXPUBKeys(seed)[0]

                    if distributer.walletIndex == 0:
                        distributer.walletIndex = getNextIndex()

                    distributer.address = BIP44Tools.getAddressesFromXPUB(xpub, distributer.walletIndex + 1)[distributer.walletIndex]
                    distributer.put()

        self.redirect('/admin?')

class DoDistributing(webapp2.RequestHandler):
    def get(self):

        distributers_query = Distributer.query(Distributer.status == 'Active')
        distributers = distributers_query.fetch()

        for distributer in distributers:
            self.distribute(distributer)





    def distribute(self, distributer):

        data = {}
        url = 'https://blockchaindata.appspot.com/utxos?confirmations=' + str(REQUIRED_CONFIRMATIONS) + '&addresses=' + str(distributer.address)
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            data = {}

        UTXOs = []
        if 'success' in data and data['success'] == 1:
            UTXOs = data['UTXOs']

        if len(UTXOs) > 0:
            self.response.write("<br>Found UTXO(s) for: " + str(distributer.name) + " on " + str(distributer.address))
            logging.info("Found UTXO(s) for: " + str(distributer.name) + " on " + str(distributer.address))

        totalInputValue = 0
        for UTXO in UTXOs:
            totalInputValue += UTXO['value']


        if totalInputValue >= distributer.threshold:
            self.response.write('<br>Distributing ' + str(totalInputValue) + ' Satoshis, minimum output: ' + str(distributer.minimumAmount) + ' fee: ' + '10000')
            logging.info('Distributing ' + str(totalInputValue) + ' Satoshis, minimum output: ' + str(distributer.minimumAmount) + ' fee: ' + '10000')

            if distributer.distributionSource == 'SIL':
                url = 'http://simplifiedinputslist.appspot.com/SIL?format=json&address=' + str(distributer.registrationAddress) + '&block=' + str(distributer.registrationBlockheight)

            elif distributer.distributionSource in ['LBL', 'LRL', 'LSL']:
                url = 'http://blocklinker.appspot.com/LinkedList?format=json&address=' + str(distributer.registrationAddress) + '&xpub=' + str(distributer.registrationXPUB) + '&block=' + str(distributer.registrationBlockheight) + '&metric=' + distributer.distributionSource


            data = {}
            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
            except:
                data = {}

            if 'success' in data and data['success'] == 1 or distributer.distributionSource == 'Custom':
                distribution = []

                if distributer.distributionSource in ['LBL', 'LRL', 'LSL', 'SIL']:
                    distribution = data[distributer.distributionSource]
                elif distributer.distributionSource == 'Custom':
                    distribution = json.loads(distributer.custom)


                if self.validateDistribution(distribution) == False:
                    self.response.write('<br><br>Warning: invalid distribution<br>')
                    self.response.write(distribution)
                    logging.error('invalid distribution: ' + str(distribution))
                else:
                    self.response.write('<br>')
                    self.response.write(distribution)
                    logging.info("distribution: " + str(distribution))
                    optimalOutputs = self.optimalOutputs(totalInputValue, distribution, distributer)
                    self.response.write('<br><br>Ouputs:<br>')
                    self.response.write(optimalOutputs)
                    logging.info("optimal outputs: " + str(optimalOutputs))


                    success = False
                    privKeys = {}
                    if distributer.addressType == 'PrivKey':
                        address = bitcoin.privtoaddr(distributer.privateKey)
                        privKeys = {address: distributer.privateKey}

                    elif distributer.addressType == 'BIP44':
                        parameters = Parameters.get_or_insert('DefaultConfig')
                        if parameters and parameters.walletseed != '' and parameters.walletseed != None:
                            seed = parameters.walletseed
                            xprivKeys = BIP44Tools.getTrezorXPRIVKeys(seed, "", 1)
                            privKeys = BIP44Tools.getPrivKey(xprivKeys[0], distributer.walletIndex)


                    if distributer.distributionSource == 'SIL' and distributer.address == distributer.registrationAddress:
                        self.response.write("<br>Dark magic detected! It looks like you are trying to set up an automated ponzi scheme, this is illegal!! Ending distribution.")
                        logging.error("Dark magic detected! It looks like you are trying to set up an automated ponzi scheme, this is illegal!! Ending distribution.")

                    elif len(optimalOutputs) > 0:
                        totalOutputValue = 0
                        for tx_output in optimalOutputs:
                            totalOutputValue += tx_output['value']

                        totalFee = totalInputValue - totalOutputValue
                        self.response.write("<br><br>Sending " + str(totalInputValue) + ' Satoshis to ' + str(len(optimalOutputs)) + ' recipients with a total fee of ' + str(totalFee))
                        logging.info("Sending " + str(totalInputValue) + ' Satoshis to ' + str(len(optimalOutputs)) + ' recipients with a total fee of ' + str(totalFee))
                        success = self.sendCustomTransaction(privKeys, UTXOs, optimalOutputs, totalFee)

                    else:
                        self.response.write("<br>Unable to calculate optimal outputs!")
                        logging.warning("Unable to calculate optimal outputs!")


                    if success == True:
                        self.response.write("<br>Success<br><br>" )
                        logging.info("Success")

                    else:
                        self.response.write("<br>Failed to send transaction<br><br>" )
                        logging.error("Failed to send transaction")

            else:
                self.response.write("<br>Failed to retrieve distribution<br><br>" )
                logging.error("Failed to retrieve distribution" )


    def validateDistribution(self, distribution):
        valid = False
        if isinstance(distribution, list):
            for i in range(0, len(distribution)):
                if isinstance(distribution[i], list):
                    if len(distribution[i]) >= 2:
                        if (isinstance(distribution[i][0], str) or isinstance(distribution[i][0], unicode)) and isinstance(distribution[i][1], int):
                            valid = True
                        else:
                            valid = False
                            break

        return valid





    def optimalOutputs(self, amount, distribution, distributer):
        optimal = []
        valueToDistribute = amount-distributer.transactionFee

        if distributer.feePercent != 0 and distributer.feeAddress != '':
            distributingFee = int(valueToDistribute * (distributer.feePercent / 100.0))
            if distributingFee < 10000:
                distributingFee = 10000

            valueToDistribute -= distributingFee
            optimal.append({'address': distributer.feeAddress, 'value': distributingFee})

        sortedDistribution = sorted(distribution, key=lambda  x: x[1], reverse=True)

        for i in range(len(sortedDistribution)-1, -1, -1):
            tmpTotal = 0
            for j in range(0, len(sortedDistribution)):
                tmpTotal += sortedDistribution[j][1]

            share = sortedDistribution[i][1]/float(tmpTotal)

            if share*valueToDistribute < distributer.minimumAmount:
                del sortedDistribution[i]
            else:
                optimal.append({'address': sortedDistribution[i][0], 'value': int(share*valueToDistribute)})

        return optimal


    def sendCustomTransaction(self, privkeys, inputs, outputs, fee=0):

        success = False
        totalInputValue = 0
        UTXOs = []
        for tx_input in inputs:
            if 'spend' not in tx_input:
                totalInputValue += tx_input['value']
                UTXOs.append(tx_input)

        totalOutputValue = 0
        for tx_output in outputs:
            totalOutputValue += tx_output['value']

        diff = totalInputValue - totalOutputValue
        if fee != diff:
            self.response.write("<br>Warning: Fee incorrect! aborting transaction")
            logging.error("Warning: Fee incorrect! aborting transaction")
        else:
            allKeysPresent = True
            allInputsConfirmed = True
            for tx_input in UTXOs:
                if tx_input['address'] not in privkeys:
                    allKeysPresent = False

                if tx_input['block_height'] == None:
                    allInputsConfirmed = False

            if allKeysPresent == True and allInputsConfirmed == True:
                tx = bitcoin.mktx(UTXOs, outputs)
                for i in range(0, len(UTXOs)):
                    tx = bitcoin.sign(tx, i, str(privkeys[UTXOs[i]['address']]))


                bitcoin.pushtx(tx)
                success = True

        return success


class Documentation(webapp2.RequestHandler):
    def get(self):

        isAdmin = False
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        parameters = Parameters.get_or_insert('DefaultConfig')

        template_values = {
            'Title': 'Distributer documentation',
            'cssHTML': includes.get_CssHTML(),
            'metaHTML': includes.get_MetaHTML(),
            'scriptsHTML': includes.get_ScriptsHTML(),
            'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
            'logoHTML': includes.get_LogoHTML(),
            'footerHTML': includes.get_FooterHTML(),
            'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
        }

        template = JINJA_ENVIRONMENT.get_template('documentation.html')

        self.response.write(template.render(template_values))




class ConfirmPage(webapp2.RequestHandler):
    def get(self):

        isAdmin = False
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        parameters = Parameters.get_or_insert('DefaultConfig')

        distributerID = 0
        distributer = Distributer(parent=distributers_key())
        error = ''
        if self.request.get('distributerID'):
            try:
                distributerID = int(self.request.get('distributerID'))
                distributer = Distributer.get_by_id(distributerID, parent=distributers_key())
            except ValueError:
                error = "distributerID must be an integer"

        template_values = {
            'Title': 'Confirm delete',
            'distributerID': distributerID,
            'distributer': distributer,
            'error': error,
            'cssHTML': includes.get_CssHTML(),
            'metaHTML': includes.get_MetaHTML(),
            'scriptsHTML': includes.get_ScriptsHTML(),
            'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
            'logoHTML': includes.get_LogoHTML(),
            'footerHTML': includes.get_FooterHTML(),
            'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
        }

        template = JINJA_ENVIRONMENT.get_template('confirm.html')

        self.response.write(template.render(template_values))

class DeleteDistributer(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def get(self):
        if users.get_current_user() and self.request.get('distributerID'):
            if self.request.get('distributerID'):
                try:
                    distributerID = int(self.request.get('distributerID'))
                    distributer = Distributer.get_by_id(distributerID, parent=distributers_key())
                    distributer.key.delete()
                    self.redirect("/admin")

                except ValueError:
                    error = "distributerID must be an integer"
        self.redirect("/admin")


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/distributer', MainPage),
    ('/documentation', Documentation),
    ('/editDistributer', EditDistributer),
    ('/saveDistributer', SaveDistributer),
    ('/updateDistributer', UpdateDistributer),
    ('/admin', AdminPage),
    ('/getAddress', GetAddress),
    ('/doDistributing', DoDistributing),
    ('/deleteDistributer', DeleteDistributer),
    ('/confirm', ConfirmPage),
], debug=True)

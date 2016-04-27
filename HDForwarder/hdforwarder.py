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
import bitcoin
import includes
import re
from google.appengine.api import urlfetch
urlfetch.set_default_fetch_deadline(60)

SOCIALBUTTONS_ENABLED = True
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

def forwarders_key():
    #Constructs a Datastore key for a Forwarder entity
    return ndb.Key('HDForward', 'HDForward')

def getNextIndex():
    i = 0
    forwarders_query = Forwarder.query(ancestor=forwarders_key()).order(-Forwarder.walletIndex)
    forwarders = forwarders_query.fetch()

    if len(forwarders) > 0:
        i = forwarders[0].walletIndex + 1

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



class Forwarder(ndb.Model):
    userID = ndb.StringProperty('u', indexed=True)
    addressType = ndb.StringProperty('t', choices=['BIP44', 'PrivKey'], default='BIP44')
    walletIndex = ndb.IntegerProperty('i', indexed=True, default=0)
    privateKey = ndb.StringProperty('p', indexed=False, default='')
    creator = ndb.StringProperty('c', default='')
    creatorEmail = ndb.StringProperty('e', default='')
    name = ndb.StringProperty('n', indexed=True, default='')
    address = ndb.StringProperty('a', indexed=True, default='')
    xpub = ndb.StringProperty('x', indexed=True, default='')
    minimumAmount = ndb.IntegerProperty('m', default=0)
    date = ndb.DateTimeProperty('dt', auto_now_add=True)
    description = ndb.TextProperty('d', default='')
    youtube = ndb.StringProperty('y', default='')
    status = ndb.StringProperty('s', choices=['Pending', 'Active', 'Disabled'], default='Pending')
    visibility = ndb.StringProperty('v', choices=['Public', 'Private'], default='Private')
    feePercent = ndb.FloatProperty('fp', default=0.0)
    feeAddress = ndb.StringProperty('fa', default='')
    confirmAmount = ndb.IntegerProperty('ca', indexed=False, default=0)






class MainPage(webapp2.RequestHandler):

    def get(self):
        error = ''
        forwarderID = 0
        LBL = []
        LAL = []
        beneficiaryAddress = ''
        beneficiaryBalance = 0
        beneficiaryShare = 0
        linkedAddress = ''

        forwardingAddress = ''
        forwardingAddressBalance = 0
        forwardingAddressBeneficiary = ''
        forwardingBeneficiaryShare = 0

        showWarning = True

        parameters = Parameters.get_or_insert('DefaultConfig')

        if self.request.get('forwarderID'):
            try:
                forwarderID = int(self.request.get('forwarderID'))
            except ValueError:
                error = 'forwarderID must be an integer'

            if error == '':
                forwarders = [Forwarder.get_by_id(forwarderID, parent=forwarders_key())]


                url = parameters.blocklinkerURL + '/LinkedList?format=json&address=' + forwarders[0].address + '&xpub=' + forwarders[0].xpub + '&metric=LBL,LAL'
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
                if 'success' in data and data['success'] == 1:
                    LBL = data['LBL']
                    LAL = data['LAL']



                if self.request.get('address'):
                    address = self.request.get('address')

                    totalShares = 0
                    for i in range(0, len(LAL)):
                        totalShares += LBL[i][1]
                        if LAL[i][0] == address:
                            beneficiaryAddress = address
                            beneficiaryBalance = LBL[i][1]
                            linkedAddress = LAL[i][1]
                            showWarning = False

                        if LAL[i][1] == address:
                            forwardingAddress = LAL[i][1]
                            forwardingAddressBalance = LBL[i][1]
                            forwardingAddressBeneficiary = LAL[i][0]
                            showWarning = False


                    if totalShares > 0:
                        beneficiaryShare = beneficiaryBalance/float(totalShares)*100
                        forwardingBeneficiaryShare = forwardingAddressBalance/float(totalShares)*100

                else:
                    showWarning = False

        else:
            showWarning = False
            forwarders_query = Forwarder.query(Forwarder.visibility == 'Public', Forwarder.status == 'Active').order(-Forwarder.date)
            forwarders = forwarders_query.fetch()

        isAdmin = False
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        if self.request.get('forwarderID') and self.request.get('format') == 'json':
            response = {'success': 1, 'forwarder': {}}
            if len(forwarders) == 1:
                forwarder = forwarders[0]
                tmpForwarder = {}
                tmpForwarder['ID'] = forwarder.key.id()
                tmpForwarder['Name'] = forwarder.name
                tmpForwarder['Address'] = forwarder.address
                tmpForwarder['Description'] = forwarder.description
                tmpForwarder['Creator'] = forwarder.creator
                tmpForwarder['CreatorEmail'] = forwarder.creatorEmail
                tmpForwarder['Youtube'] = forwarder.youtube
                tmpForwarder['Status'] = forwarder.status
                tmpForwarder['ConfirmAmount'] = forwarder.confirmAmount
                tmpForwarder['FeeAddress'] = forwarder.feeAddress
                tmpForwarder['FeePercent'] = forwarder.feePercent
                tmpForwarder['MinimumAmount'] = forwarder.minimumAmount
                tmpForwarder['XPUB'] = forwarder.xpub
                tmpForwarder['Visibility'] = forwarder.visibility
                tmpForwarder['Date'] = int(time.mktime(forwarder.date.timetuple()))
                response['forwarder'] = tmpForwarder


            self.response.write(json.dumps(response))

        elif not self.request.get('forwarderID') and self.request.get('format') == 'json':
            response = {'success': 1, 'forwarders': []}
            for forwarder in forwarders:
                tmpForwarder = {}
                tmpForwarder['ID'] = forwarder.key.id()
                tmpForwarder['Name'] = forwarder.name
                tmpForwarder['Address'] = forwarder.address
                tmpForwarder['Description'] = forwarder.description
                tmpForwarder['Creator'] = forwarder.creator
                tmpForwarder['CreatorEmail'] = forwarder.creatorEmail
                tmpForwarder['Youtube'] = forwarder.youtube
                tmpForwarder['Status'] = forwarder.status
                tmpForwarder['ConfirmAmount'] = forwarder.confirmAmount
                tmpForwarder['FeeAddress'] = forwarder.feeAddress
                tmpForwarder['FeePercent'] = forwarder.feePercent
                tmpForwarder['MinimumAmount'] = forwarder.minimumAmount
                tmpForwarder['XPUB'] = forwarder.xpub
                tmpForwarder['Visibility'] = forwarder.visibility
                tmpForwarder['Date'] = int(time.mktime(forwarder.date.timetuple()))
                response['forwarders'].append(tmpForwarder)


            self.response.write(json.dumps(response))

        else:
            template_values = {
                'url': url,
                'url_linktext': url_linktext,

                'forwarders': forwarders,
                'forwarderID': forwarderID,

                'showWarning': showWarning,

                'beneficiaryAddress': beneficiaryAddress,
                'beneficiaryBalance' : beneficiaryBalance,
                'beneficiaryShare': '%.2f' % beneficiaryShare,
                'linkedAddress': linkedAddress,

                'forwardingAddress': forwardingAddress,
                'forwardingAddressBalance' : forwardingAddressBalance,
                'forwardingAddressBeneficiary':  forwardingAddressBeneficiary,
                'forwardingBeneficiaryShare': '%.2f' % forwardingBeneficiaryShare,


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



class ForwarderPage(webapp2.RequestHandler):

    def get(self):
        error = ''
        isAdmin = False

        forwarderID = 0
        forwarder = Forwarder(parent=forwarders_key())
        if self.request.get('forwarderID'):
            try:
                forwarderID = int(self.request.get('forwarderID'))
            except ValueError:
                error = 'forwarderID must be an integer'

            if error == '':
                forwarder = Forwarder.get_by_id(forwarderID, parent=forwarders_key())

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
            if forwarderID == 0:
                forwarder.userID = users.get_current_user().user_id()
                forwarder.creator = users.get_current_user().nickname()
                forwarder.creatorEmail = users.get_current_user().email()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'


        parameters = Parameters.get_or_insert('DefaultConfig')
        template_values = {
            'url': url,
            'url_linktext': url_linktext,

            'forwarder': forwarder,
            'forwarderID': forwarderID,

            'cssHTML': includes.get_CssHTML(),
            'metaHTML': includes.get_MetaHTML(),
            'scriptsHTML': includes.get_ScriptsHTML(),
            'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
            'logoHTML': includes.get_LogoHTML(),
            'footerHTML': includes.get_FooterHTML(),
            'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
        }

        template = JINJA_ENVIRONMENT.get_template('forwarder.html')
        self.response.write(template.render(template_values))


class SaveForwarder(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def post(self):
        error = ''
        forwarderID = 0
        if self.request.get('ForwarderID'):
            try:
                forwarderID = int(self.request.get('ForwarderID'))
            except ValueError:
                error = 'forwarderID must be an integer'

            if error == '':
                forwarder = Forwarder(parent=forwarders_key())
                if forwarderID not in ['', 0, 'None']:
                    forwarder = Forwarder.get_by_id(forwarderID, parent=forwarders_key())

                forwarder.name = self.request.get('ForwarderName')
                forwarder.description = self.request.get('Description')
                forwarder.creator = self.request.get('Creator')
                forwarder.creatorEmail = self.request.get('CreatorEmail')


                forwarder.walletIndex = int(self.request.get('WalletIndex'))
                forwarder.privateKey = self.request.get('PrivateKey')
                forwarder.addressType = self.request.get('AddressType')

                forwarder.xpub = self.request.get('XPUB')
                forwarder.minimumAmount = int(self.request.get('MinimumAmount'))
                forwarder.youtube = self.request.get('Youtube')
                if self.request.get('Visibility') in ['Public', 'Private']:
                    forwarder.visibility = self.request.get('Visibility')

                if self.request.get('Status') in ['Pending', 'Active', 'Disabled']:
                    forwarder.status = self.request.get('Status')

                forwarder.feePercent = float(self.request.get('FeePercent'))
                forwarder.feeAddress = self.request.get('FeeAddress')

                forwarder.confirmAmount = int(self.request.get('ConfirmAmount'))


                forwarder_key = forwarder.put()
                self.redirect('/getAddress?id=' + str(forwarder_key.id()))


class UpdateForwarder(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def post(self):
        error = ''
        forwarderID = 0
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
                forwarderID = int(self.request.get('ID'))
            except ValueError:
                error = 'ID must be an integer'
                response = {'success': 0, 'error': error}

            if error == '':
                forwarder = Forwarder(parent=forwarders_key())
                if forwarderID != 0:
                    forwarder = Forwarder.get_by_id(forwarderID, parent=forwarders_key())

                if self.request.get('Name'):
                    if len(self.request.get('Name')) > 0:
                        forwarder.name = self.request.get('Name')
                    else:
                        error = 'Name cannot be empty'

                if self.request.get('Description'):
                    forwarder.description = self.request.get('Description')

                if self.request.get('Creator'):
                    forwarder.creator = self.request.get('Creator')

                if self.request.get('CreatorEmail'):
                    if validEmail(self.request.get('CreatorEmail')):
                        forwarder.creatorEmail = self.request.get('CreatorEmail')
                    else:
                        error = 'Invalid email address'

                if self.request.get('XPUB'):
                    if validXPUB(self.request.get('XPUB')):
                        forwarder.xpub = self.request.get('XPUB')
                    else:
                        error = 'Invalid XPUB key'

                if len(forwarder.xpub) == 0:
                    error = 'XPUB key cannot be empty'


                if self.request.get('MinimumAmount'):
                    amount = -1
                    try:
                        amount = int(self.request.get('MinimumAmount'))
                    except ValueError:
                        error = 'MinimumAmount must be a positive integer or equal to 0 (in Satoshis)'

                    if amount >= 0:
                        forwarder.minimumAmount = amount
                    else:
                        error = 'MinimumAmount must be a positive integer or equal to 0 (in Satoshis)'

                if self.request.get('Youtube'):
                    forwarder.youtube = self.request.get('Youtube')

                if self.request.get('Visibility'):
                    if self.request.get('Visibility') in ['Public', 'Private']:
                        forwarder.visibility = self.request.get('Visibility')
                    else:
                        error = 'Visibility must be Public or Private'

                if self.request.get('Status'):
                    if self.request.get('Status') in ['Pending', 'Active', 'Disabled']:
                        forwarder.status = self.request.get('Status')
                    else:
                        error = 'Status must be Pending, Active or Disabled'

                if self.request.get('FeePercent'):
                    percentage = -1
                    try:
                        percentage = float(self.request.get('FeePercent'))
                    except ValueError:
                        error = 'Incorrect Fee percentage'

                    if percentage >= 0:
                        forwarder.feePercent = percentage
                    else:
                        error = 'FeePercent must be greater than or equal to 0'

                if self.request.get('FeeAddress'):
                    forwarder.feeAddress = self.request.get('FeeAddress')

                if self.request.get('ConfirmAmount'):
                    amount = -1
                    try:
                        amount = int(self.request.get('ConfirmAmount'))
                    except ValueError:
                        error = 'ConfirmAmount must be a positive integer or equal to 0 (in Satoshis)'

                    if amount >= 0:
                        forwarder.confirmAmount = amount
                    else:
                        error = 'ConfirmAmount must be greater than or equal to 0 (in Satoshis)'


                if self.request.get('AddressType'):
                    if self.request.get('AddressType') in ['PrivKey', 'BIP44']:
                        forwarder.addressType = self.request.get('AddressType')
                    else:
                        error = 'AddressType must be BIP44 or PrivKey'

                if self.request.get('WalletIndex'):
                    index = -1
                    try:
                        index = int(self.request.get('WalletIndex'))
                    except ValueError:
                        error = 'WalletIndex must be a positive integer'

                    if index >= 0:
                        forwarder.walletIndex = index
                    else:
                        error = 'Wallet index must be greater than or equal to 0'

                if self.request.get('PrivateKey'):
                    forwarder.privateKey = self.request.get('PrivateKey')


                if error == '':
                    forwarder.put()

                    if forwarder.addressType == 'PrivKey' and forwarder.privateKey != '':
                        newAddress = bitcoin.privtoaddr(forwarder.privateKey)
                        if forwarder.address != newAddress:
                            forwarder.address = newAddress
                            forwarder.put()
                    elif forwarder.addressType == 'BIP44':
                        if parameters and (parameters.walletseed != None and parameters.walletseed != ""):
                            if forwarder.walletIndex == 0:
                                forwarder.walletIndex = getNextIndex()
                                #bugfix: when creating the first forwarder, set index to 1
                                if forwarder.walletIndex == 0:
                                    forwarder.walletIndex = 1

                                seed = parameters.walletseed
                                xpub = BIP44Tools.getTrezorXPUBKeys(seed)[0]
                                forwarder.address = BIP44Tools.getAddressesFromXPUB(xpub, forwarder.walletIndex + 1)[forwarder.walletIndex]
                                forwarder.put()


                    response['success'] = 1
                    tmpForwarder = {}
                    tmpForwarder['ID'] = forwarder.key.id()
                    tmpForwarder['Name'] = forwarder.name
                    tmpForwarder['Address'] = forwarder.address
                    tmpForwarder['Description'] = forwarder.description
                    tmpForwarder['Creator'] = forwarder.creator
                    tmpForwarder['CreatorEmail'] = forwarder.creatorEmail
                    tmpForwarder['Youtube'] = forwarder.youtube
                    tmpForwarder['Status'] = forwarder.status
                    tmpForwarder['ConfirmAmount'] = forwarder.confirmAmount
                    tmpForwarder['FeeAddress'] = forwarder.feeAddress
                    tmpForwarder['FeePercent'] = forwarder.feePercent
                    tmpForwarder['MinimumAmount'] = forwarder.minimumAmount
                    tmpForwarder['XPUB'] = forwarder.xpub
                    tmpForwarder['Visibility'] = forwarder.visibility
                    tmpForwarder['Date'] = int(time.mktime(forwarder.date.timetuple()))
                    response['forwarder'] = tmpForwarder

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

        forwarderID = 0
        status = 'All'
        if self.request.get('status') in ['Pending', 'Active', 'Disabled']:
            status = self.request.get('status')

        if status != 'All':
            forwarders_query = Forwarder.query(Forwarder.status == status).order(-Forwarder.date)
        else:
            forwarders_query = Forwarder.query().order(-Forwarder.date)

        forwarders = forwarders_query.fetch()

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
            'forwarders': forwarders,
            'forwarderID': forwarderID,
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
            forwarder = Forwarder.get_by_id(id, parent=forwarders_key())

            if forwarder.addressType == 'PrivKey' and forwarder.privateKey != '':
                forwarder.address =  bitcoin.privtoaddr(forwarder.privateKey)
                forwarder.put()


            elif forwarder.addressType == 'BIP44':
                parameters = Parameters.get_or_insert('DefaultConfig')

                if parameters and (parameters.walletseed != None and parameters.walletseed != ""):
                    seed = parameters.walletseed
                    xpub = BIP44Tools.getTrezorXPUBKeys(seed)[0]

                    if forwarder.walletIndex == 0:
                        forwarder.walletIndex = getNextIndex()

                    forwarder.address = BIP44Tools.getAddressesFromXPUB(xpub, forwarder.walletIndex + 1)[forwarder.walletIndex]
                    forwarder.put()


        self.redirect('/admin?')

class DoForwarding(webapp2.RequestHandler):
    def get(self):

        forwarders_query = Forwarder.query(Forwarder.status == 'Active')
        forwarders = forwarders_query.fetch()

        for forwarder in forwarders:
            self.forward(forwarder)





    def forward(self, forwarder):
        data = {}
        parameters = Parameters.get_or_insert('DefaultConfig')
        url = parameters.blockchaindataURL + '/utxos?confirmations=' + str(REQUIRED_CONFIRMATIONS) + '&addresses=' + str(forwarder.address)
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            data = {}

        if 'success' in data and data['success'] == 1 and 'UTXOs' in data:
            if len(data['UTXOs']) > 0:
                self.response.write("<br>Found UTXO(s) for: " + str(forwarder.name) + " on " + str(forwarder.address))
                logging.info("Found UTXO(s) for: " + str(forwarder.name) + " on " + str(forwarder.address))

            for UTXO in data['UTXOs']:
                self.response.write('<br>Forwarding ' + str(UTXO['value']) + ' from tx ' + UTXO['output'])
                logging.info('Forwarding ' + str(UTXO['value']) + ' from tx ' + UTXO['output'])

                to_addresses = []
                amounts = []

                data = {}
                url = parameters.blockchaindataURL + '/primeInputAddress?txid=' + UTXO['output'].split(":")[0]
                try:
                    ret = urllib2.urlopen(urllib2.Request(url))
                    data = json.loads(ret.read())
                except:
                    data = {}

                if 'success' in data and data['success'] == 1:
                    primeInputAddress = data['PrimeInputAddress']
                else:
                    continue



                url = parameters.blocklinkerURL + '/?address=' + str(forwarder.address) + '&xpub=' + forwarder.xpub + '&metric=LAL&format=json'
                data = {}
                try:
                    ret = urllib2.urlopen(urllib2.Request(url))
                    data = json.loads(ret.read())
                except:
                    data = {}

                if 'success' in data and data['success'] == 1 :
                    LAL = data['LAL']
                    for i in range(0, len(LAL)):
                        if LAL[i][0] == primeInputAddress:
                            to_addresses.append(LAL[i][1])
                            amounts.append(UTXO['value'])

                    success = False
                    privKeys = {}
                    if forwarder.addressType == 'PrivKey':
                        address = bitcoin.privtoaddr(forwarder.privateKey)
                        privKeys = {address: forwarder.privateKey}

                    elif forwarder.addressType == 'BIP44':
                        parameters = Parameters.get_or_insert('DefaultConfig')
                        if parameters and parameters.walletseed != '' and parameters.walletseed != None:
                            seed = parameters.walletseed
                            xprivKeys = BIP44Tools.getTrezorXPRIVKeys(seed, "", 1)
                            privKeys = BIP44Tools.getPrivKey(xprivKeys[0], forwarder.walletIndex)


                    if len(amounts) > 0 and forwarder.minimumAmount > 0 and amounts[0] < forwarder.minimumAmount:
                        self.response.write("<br>" + str(amounts[0]) + " is below minimum of " + str(forwarder.minimumAmount) + "! returning btc to sender")
                        logging.warning(str(amounts[0]) + " is below minimum of " + str(forwarder.minimumAmount) + "! returning btc to sender")
                        to_addresses = [primeInputAddress]

                        #if there is enough btc, subtract network fee, otherwise log a warning
                        if amounts[0] > TRANSACTION_FEE:
                            #subtract network fee in satoshis from first amount
                            amounts[0] = amounts[0] - TRANSACTION_FEE

                            outputs = []
                            outputs.append({'address': to_addresses[0], 'value': amounts[0]})
                            self.response.write("<br>Returning " + str(amounts[0]) + " to " + to_addresses[0])
                            logging.info("Returning " + str(amounts[0]) + " to " + to_addresses[0])
                            success = self.sendCustomTransaction(privKeys, [UTXO], outputs, TRANSACTION_FEE)


                        else:
                            self.response.write("<br>Insufficient amount to send, please remove UTXO manually as soon as possible.")
                            logging.warning("Insufficient amount to send, please remove UTXO manually as soon as possible.")



                    elif len(to_addresses) > 0:
                        if forwarder.feePercent > 0.0 and forwarder.feeAddress != '':
                            fee = int(amounts[0] * forwarder.feePercent/100)
                            amounts = [amounts[0] - fee, fee]
                            to_addresses.append(forwarder.feeAddress)
                            self.response.write("<br>Forwarding Fee: " + str(amounts[1]) + " -> " + str(to_addresses[1]))
                            logging.info("Forwarding Fee: " + str(amounts[1]) + " -> " + str(to_addresses[1]))

                        if forwarder.confirmAmount > 0:
                            amounts[0] -= forwarder.confirmAmount
                            amounts.append(forwarder.confirmAmount)
                            to_addresses.append(primeInputAddress)
                            self.response.write("<br>Origin: " + str(forwarder.confirmAmount) + " -> " + primeInputAddress)
                            logging.info("Origin: " + str(forwarder.confirmAmount) + " -> " + primeInputAddress)



                        #subtract transaction fee in satoshis from first amount
                        amounts[0] = amounts[0] - TRANSACTION_FEE

                        self.response.write("<br>Destination: " + str(amounts[0]) + " -> " + to_addresses[0])
                        logging.info("Destination: " + str(amounts[0]) + " -> " + to_addresses[0])

                        if amounts[0] > 0:
                            outputs = []
                            for i in range(0, len(amounts)):
                                outputs.append({'address': to_addresses[i], 'value': amounts[i]})

                            success = self.sendCustomTransaction(privKeys, [UTXO], outputs, TRANSACTION_FEE)
                        else:
                            self.response.write("Not enough balance left to send Transaction")
                            logging.error("Not enough balance left to send Transaction")

                    if success == True:
                        self.response.write("<br>Success<br><br>" )
                        logging.info("Success")

                    else:
                        self.response.write("<br>Failed to send transaction<br><br>" )
                        logging.error("Failed to send transaction")

                else:
                    self.response.write("<br>Failed to retrieve data from blocklinker<br><br>" )
                    logging.error("Failed to retrieve data from blocklinker" )



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
            'Title': 'HDForwarder documentation',
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

        forwarderID = 0
        forwarder = Forwarder(parent=forwarders_key())
        error = ''
        if self.request.get('forwarderID'):
            try:
                forwarderID = int(self.request.get('forwarderID'))
                forwarder = Forwarder.get_by_id(forwarderID, parent=forwarders_key())
            except ValueError:
                error = "forwarderID must be an integer"

        template_values = {
            'Title': 'Confirm delete',
            'forwarderID': forwarderID,
            'forwarder': forwarder,
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

class DeleteForwarder(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def get(self):
        if users.get_current_user() and self.request.get('forwarderID'):
            if self.request.get('forwarderID'):
                try:
                    forwarderID = int(self.request.get('forwarderID'))
                    forwarder = Forwarder.get_by_id(forwarderID, parent=forwarders_key())
                    forwarder.key.delete()
                    self.redirect("/admin")

                except ValueError:
                    error = "forwarderID must be an integer"
        self.redirect("/admin")

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/forwarder', MainPage),
    ('/documentation', Documentation),
    ('/updateForwarder', UpdateForwarder),
    ('/editForwarder', ForwarderPage),
    ('/saveForwarder', SaveForwarder),
    ('/admin', AdminPage),
    ('/getAddress', GetAddress),
    ('/doForwarding', DoForwarding),
    ('/confirm', ConfirmPage),
    ('/deleteForwarder', DeleteForwarder),

], debug=True)

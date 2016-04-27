import os
import jinja2
import webapp2
import urllib2
import json

from google.appengine.ext import ndb
from google.appengine.api import urlfetch
urlfetch.set_default_fetch_deadline(45)
import includes
import bitcoin
import re




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

def validAddress(address):
    valid = False
    if re.match("^[13][a-km-zA-HJ-NP-Z0-9]{26,33}$", address):
        valid = True

    return valid

def validXPUB(xpub):
    valid =False
    if xpub[:4] == "xpub":
        valid = True

    return valid


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.address = ''
        self.block = 0
        self.xpub = ''
        metrics = ['LBL'] #default metric(s)
        linkedAddresses = []
        balances = []
        error = ''

        if self.request.get('address') != '':
            address = self.request.get('address')
            if validAddress(address):
                self.address = address
            else:
                error = "Invalid address: " + address

        if self.request.get('xpub') != '':
            xpub = self.request.get('xpub')
            if validXPUB(xpub):
                self.xpub = xpub
            else:
                error = "Invalid XPUB key: " + xpub

        if self.request.get('block') != '':
            try:
                self.block = int(self.request.get('block'))
            except ValueError:
                error = "Block must be a positive integer"

        if self.request.get('metric') != '':
            metrics = str(self.request.get('metric')).split(",")

        SIL = []
        data = {}
        if self.address != '' and self.xpub != '' and error == '':
            parameters = Parameters.get_or_insert('DefaultConfig')
            url = parameters.simplifiedInputsListURL + '/SIL?format=json&address=' + self.address

            if self.block != 0:
                url += '&block=' + str(self.block)

            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
            except:
                data = {}

            if 'success' in data and data['success'] == 1:
                SIL = data['SIL']
                linkedAddresses = self.getAddressesFromXPUB(self.xpub, len(SIL))
                balances = self.getBalances(linkedAddresses)




        LAL = [] #Linked Address List
        LBL = [] #Linked Balance List
        LRL = [] #Linked Received List
        LSL = [] #Linked Sent List

        response = {}

        if self.request.get('format') == 'json' and error == '':
            for i in range(0, len(SIL)):
                if 'LAL' in metrics:
                    LAL.append([SIL[i][0], linkedAddresses[i]])

                if 'LBL' in metrics:
                    LBL.append([SIL[i][0], balances[linkedAddresses[i]]['balance']])

                if 'LRL' in metrics:
                    LRL.append([SIL[i][0], balances[linkedAddresses[i]]['received']])

                if 'LSL' in metrics:
                    LSL.append([SIL[i][0], balances[linkedAddresses[i]]['sent']])

            if 'LAL' in metrics:
                response['LAL'] = LAL

            if 'LBL' in metrics:
                response['LBL'] = LBL

            if 'LRL' in metrics:
                response['LRL'] = LRL

            if 'LSL' in metrics:
                response['LSL'] = LSL

            response['success'] = 1
            self.response.write(json.dumps(response))

        elif self.request.get('format') == 'json' and error != '':
            self.response.write(json.dumps({'success': 0, 'error': error}))

        else:
            parameters = Parameters.get_or_insert('DefaultConfig')
            template_values = {
                'Title': 'Blocklinker',
                'data': data,
                'address': self.address,
                'xpub': self.xpub,
                'block': self.block,
                'SIL': SIL,
                'error': error,
                'nSIL': len(SIL),
                'linkedAddresses': linkedAddresses,
                'balances': balances,
                'metric': metrics[0],

                'cssHTML': includes.get_CssHTML(),
                'metaHTML': includes.get_MetaHTML(),
                'scriptsHTML': includes.get_ScriptsHTML(),
                'navigationHTML': includes.get_NavigationHTML(Spellbook(parameters)),
                'logoHTML': includes.get_LogoHTML(),
                'footerHTML': includes.get_FooterHTML(),
                'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
            }

            template = JINJA_ENVIRONMENT.get_template('index.html')

            self.response.write(template.render(template_values))

    #getAddressesFromXPUB will return an array of addresses generated from an XPUB key
    #optional parameters:
    #i          the amount of addresses to be generated
    #addrType   0: Receiving addresses, 1: Change addresses, ...
    def getAddressesFromXPUB(self, xpub, i=10, addrType=0):
        addressList = []
        pub0 = bitcoin.bip32_ckd(xpub, addrType)

        for i in range (0, i):
            publicKey = bitcoin.bip32_ckd(pub0, i)
            hexKey = bitcoin.encode_pubkey(bitcoin.bip32_extract_key(publicKey), 'hex_compressed')
            address_fromPub =  bitcoin.pubtoaddr(hexKey)
            addressList.append(address_fromPub)

        return addressList

    #this function will query blockchaindata.appspot.com and return a dictionary of confirmed balances
    def getBalances(self, addresses):
        balances = {}
        parameters = Parameters.get_or_insert('DefaultConfig')
        url = parameters.blockchaindataURL + '/balances?addresses=' + self.toUrlString(addresses)
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            data = {}

        if 'success' in data and data['success'] == 1:
            balances = data['balances']

        return balances

    #this function will concatenate all adresses and put '|' between them
    def toUrlString(self, addresses):
        addrString = ''
        for address in addresses:
            addrString += address + '|'

        addrString = addrString[:-1]
        return addrString


class Documentation(webapp2.RequestHandler):
    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')

        template_values = {
            'Title': 'Blocklinker documentation',
            'cssHTML': includes.get_CssHTML(),
            'metaHTML': includes.get_MetaHTML(),
            'scriptsHTML': includes.get_ScriptsHTML(),
            'navigationHTML': includes.get_NavigationHTML(Spellbook(parameters)),
            'logoHTML': includes.get_LogoHTML(),
            'footerHTML': includes.get_FooterHTML(),
            'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
        }

        template = JINJA_ENVIRONMENT.get_template('documentation.html')

        self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/documentation', Documentation),
    ('/LinkedList', MainHandler),

], debug=True)

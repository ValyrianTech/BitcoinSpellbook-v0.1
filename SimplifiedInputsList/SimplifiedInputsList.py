import os

import jinja2
import webapp2
import urllib2
import json
import re
import includes

from google.appengine.ext import ndb
from google.appengine.api import urlfetch
urlfetch.set_default_fetch_deadline(45)

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


class MainHandler(webapp2.RequestHandler):
    def get(self):
        error = ''
        self.address = ''
        self.block = 0

        SIL = []

        if self.request.get('address') != '':
            self.address = self.request.get('address')


        if validAddress(self.address) or self.address == '':
            parameters = Parameters.get_or_insert('DefaultConfig')
            url = parameters.blockchaindataURL + '/latestBlock'
            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
            except:
                data = {}


            latestBlock = 0
            if 'success' in data and data['success'] == 1:
                latestBlock = data['latestBlock']['height']
            else:
                error = 'Unable to retrieve latest block'

            self.block = latestBlock
            if self.request.get('block') != '' and self.request.get('block') != '0':
                try:
                    self.block = int(self.request.get('block'))
                except ValueError:
                    self.block = 0
                    error = "block must be a positive integer"


            txs = []
            if self.address != '' and self.block != 0:
                url = parameters.blockchaindataURL + '/transactions?format=json&address=' + self.address + '&block=' + str(self.block)
                try:
                    ret = urllib2.urlopen(urllib2.Request(url))
                    data = json.loads(ret.read())
                except:
                    data = {}


                txs = []
                if 'success' in data and data['success'] == 1:
                    txs = data['TXS']

                else:
                    error = 'Unable to retrieve transactions'


            SIL = self.TXS2SIL(txs, self.block)

        else:
            error = 'Invalid address: ' + self.address

        if self.request.get('format') == 'json' and error == '':
            self.response.write(json.dumps({'success': 1, 'SIL': SIL}))

        elif self.request.get('format') == 'json' and error != '':
            self.response.write(json.dumps({'success': 0, 'error': error}))

        else:
            parameters = Parameters.get_or_insert('DefaultConfig')
            template_values = {
                'Title': 'Simplified Inputs List',
                'address': self.address,
                'block': self.block,
                'SIL': SIL,
                'error': error,
                'nSIL': len(SIL),
                'totalReceived': self.totalReceived(SIL),

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

    def TXS2SIL(self, txs, block=0):

        sortedTXS = self.sortTXS(txs)
        SIL = []
        for tx in sortedTXS:
            if tx['receiving'] == True and (block == 0 or tx['blockheight'] <= block) and tx['blockheight'] != None:
                recurring = False
                for i in range(0, len(SIL)):
                    if SIL[i][0] == tx['primeInputAddress']:
                        SIL[i][1] += tx['receivedValue']
                        recurring = True

                if recurring == False:
                    SIL.append( [tx['primeInputAddress'], tx['receivedValue'] ] )

        return SIL

    def totalReceived(self, SIL):
        total = 0
        for tx_input in SIL:
            total += tx_input[1]

        return total

    def sortTXS(self, txs):
        blockTXS = {}
        for tx in txs:
            if tx['blockheight'] in blockTXS:
                blockTXS[tx['blockheight']].append(tx)
            else:
                blockTXS[tx['blockheight']] = [tx]

        sortedTXS = []
        for block in sorted(blockTXS):
            for tx in sorted(blockTXS[block], key= lambda x: x['txid']):
                sortedTXS.append(tx)

        return sortedTXS

class Documentation(webapp2.RequestHandler):
    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')


        template_values = {
            'Title': 'Simplified Inputs List documentation',
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
    ('/SIL', MainHandler),

], debug=True)

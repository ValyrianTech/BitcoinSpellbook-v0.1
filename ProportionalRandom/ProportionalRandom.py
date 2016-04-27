import os
import jinja2
import webapp2
import urllib2
import json
import logging
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

def validXPUB(xpub):
    valid =False
    if xpub[:4] == "xpub":
        valid = True

    return valid



class MainHandler(webapp2.RequestHandler):
    def get(self):
        error = ''
        parameters = Parameters.get_or_insert('DefaultConfig')
        self.address = ''
        self.regBlock = 0
        distribution = []
        if self.request.get('address') != '':
            address = self.request.get('address')
            if validAddress(address):
                self.address = self.request.get('address')
            else:
                error = "Invalid address: " + address


        if self.request.get('regBlock') != '':
            try:
                self.regBlock = int(self.request.get('regBlock'))
            except ValueError:
                error = "Block for SIL must be a positive integer"

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
            logging.error(error)

        self.block = 0
        if self.request.get('block') != '':
            try:
                self.block = int(self.request.get('block'))
            except:
                error = "Block must be a positive integer"
        else:
            self.block = latestBlock

        hash = ''
        intHash = ''
        if latestBlock >= self.block and latestBlock > 0 and error == '':
            url = parameters.blockchaindataURL + '/block?block=' + str(self.block)
            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
            except:
                data = {}

            if 'success' in data and data['success'] == 1:
                hash = data['block']['hash']
                intHash = int(hash, 16)
            else:
                error = 'Unable to retrieve hash'
                logging.error(error)

        self.xpub = ''
        if self.request.get('xpub') != '':
            xpub = self.request.get('xpub')
            if validXPUB(xpub):
                self.xpub = self.request.get('xpub')
            else:
                error = "Invalid XPUB key: " + xpub

        self.metric = 'SIL'
        if self.request.get('metric') != '' and self.request.get('metric') in ['LBL', 'LRL', 'LSL']:
            self.metric = self.request.get('metric')



        if self.address != '' and error == '':
            distribution = self.getDistribution(self.address, self.regBlock, self.xpub, self.metric)
            distribution = self.addCumulative(distribution)

        nDistribution = len(distribution)

        strFloat = '0.'
        for i in range(len(str(intHash))-1, -1, -1):
            strFloat += str(intHash)[i]
        rand = float(strFloat)

        winnerIndex = -1
        winnerAddress = ''
        values = []
        totalValue = 0
        if nDistribution > 0 and latestBlock >= self.block:
            values = self.extractValues(distribution)
            totalValue = sum(values)
            winnerIndex = getWinnerIndex(rand, values)
            winnerAddress = distribution[winnerIndex][0]



        if self.request.get('format') == 'json' and error == '':
            self.response.write(json.dumps({'success': 1, 'winner': {'distribution': distribution, 'winnerAddress': winnerAddress, 'winnerIndex': winnerIndex, 'intHash': intHash, 'random': rand, 'target': totalValue*rand}}))

        elif self.request.get('format') == 'json' and error != '':
            self.response.write(json.dumps({'success': 0, 'error': error}))

        else:
            parameters = Parameters.get_or_insert('DefaultConfig')
            template_values = {
                'Title': 'Proportional Random',
                'address': self.address,
                'regBlock': self.regBlock,
                'block': self.block,
                'xpub': self.xpub,
                'metric': self.metric,
                'latestBlock': latestBlock,
                'hash': hash,
                'intHash': intHash,
                'rand': rand,
                'totalValue': totalValue,
                'winnerIndex': winnerIndex,
                'winnerAddress': winnerAddress,
                'distribution': distribution,
                'nDistribution': nDistribution,
                'error': error,

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

    def extractValues(self, distribution):
        values = []
        for i in range(0, len(distribution)):
            values.append(distribution[i][1])

        return values

    def addCumulative(self, distribution):
        cumul = 0
        for i in range(0, len(distribution)):
            cumul += distribution[i][1]
            distribution[i].append(cumul)

        return distribution


    def getDistribution(self, address, block, xpub='', metric='SIL'):
        distribution = []
        data= {}
        parameters = Parameters.get_or_insert('DefaultConfig')
        if metric == 'SIL':

            url = parameters.simplifiedInputsListURL + '/SIL?format=json&address=' + address + '&block=' + str(block)
            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
            except:
                data= {}

        elif metric in ['LBL', 'LRL','LSL'] and xpub != '':
            url = parameters.blocklinkerURL + '/LinkedList?format=json&address=' + address + '&block=' + str(block) + '&xpub=' + xpub + '&metric=' + metric
            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
            except:
                data= {}


        if 'success' in data:
            if data['success'] == 1:
                distribution = data[metric]



        return distribution


def getWinnerIndex(rand, values):

    choice = 0
    total = sum(values)

    if(total > 0):
        cumulative = 0.0
        for i in range(0, len(values)):
            cumulative = cumulative + values[i]
            if (cumulative >= (rand*total) ):
                choice = i
                break
    return choice

class Documentation(webapp2.RequestHandler):
    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')

        template_values = {
            'Title': 'Proportional random documentation',
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
    ('/ProportionalRandom', MainHandler),
], debug=True)

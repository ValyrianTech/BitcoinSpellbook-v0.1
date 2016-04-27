import os
import jinja2
import webapp2
import json
import logging
import re
import includes

from google.appengine.ext import ndb
from google.appengine.api import urlfetch
urlfetch.set_default_fetch_deadline(60)

import Blocktrail_com
import Blockchain_info
import Insight


def validAddress(address):
    valid = False
    if re.match("^[13][a-km-zA-HJ-NP-Z0-9]{26,33}$", address):
        valid = True

    return valid

def validAddresses(addresses):
    valid = False
    for address in addresses.split("|"):
        if validAddress(address):
            valid = True
        else:
            valid = False
            break

    return valid


def validTxid(txid):
    valid = False
    try:
        int(txid, 16)
        valid = True
    except ValueError:
        valid = False

    if len(txid) != 64:
        valid = False

    return valid

def logProviderFailures(i):
        if i == 1:
            logging.info('Primary provider failed')
        elif i == 2:
            logging.warning('Primary and Secondary provider failed')
        elif i == 3:
            logging.warning('Primary and Secondary and Tertiary provider failed')
        elif i > 3:
            logging.error('All providers failed')






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

class Providers(ndb.Model):
    #Model for 3rd party data providers parameters
    blocktrail_key = ndb.StringProperty(indexed=True, default="a8a84ed2929da8313d75d16e04be2a26c4cc4ea4")
    insight_url = ndb.StringProperty(indexed=True, default="https://blockexplorer.com/api/")




provider = Providers.get_or_insert('DefaultConfig')
blockchain = Blockchain_info.API()
blocktrail = Blocktrail_com.API(provider.blocktrail_key)
insight = Insight.API(provider.insight_url)


#list of 3rd party data providers in order of preference
providerNames = ['Blocktrail.com', 'Blockchain.info', 'Insight']
providerApis = [blocktrail, blockchain, insight]




class UTXOs(webapp2.RequestHandler):
    def get(self):
        response = {'success': 0}
        self.addresses = ''
        if self.request.get('addresses') != '':
            self.addresses = self.request.get('addresses')

        if validAddresses(self.addresses):
            for i in range(0, len(providerApis)):
                data = providerApis[i].getUTXOs(self.addresses)
                if 'success' in data and data['success'] == 1:
                    response = data
                    response['provider'] = providerNames[i]
                    break

            logProviderFailures(i)

            if response['success'] == 0:
                response['error'] = 'All data providers failed'

        else:
            logging.error('Invalid address found')
            response['error'] = 'Invalid address found'

        self.response.write(json.dumps(response))


class Balances(webapp2.RequestHandler):
    def get(self):
        response = {'success': 0}
        self.addresses = ''
        if self.request.get('addresses') != '':
            self.addresses = self.request.get('addresses')

        if validAddresses(self.addresses):
            for i in range(0, len(providerApis)):
                data = providerApis[i].getBalance(self.addresses)
                if 'success' in data and data['success'] == 1:
                    response = data
                    response['provider'] = providerNames[i]
                    break

            logProviderFailures(i)

            if response['success'] == 0:
                response['error'] = 'All data providers failed'
        else:
            logging.error('Invalid address found')
            response['error'] = 'Invalid address found'

        self.response.write(json.dumps(response))


class Block(webapp2.RequestHandler):
    def get(self):
        response = {'success': 0}
        self.blockHeight = 0
        validBlock = False
        if self.request.get('block') != '':
            try:
                self.blockHeight = int(self.request.get('block'))
                if self.blockHeight > 0:
                    validBlock = True
                else:
                    logging.error('block must be a positive integer')
                    response['error'] = 'block must be a positive integer'

            except ValueError:
                logging.error('block must be a positive integer')
                response['error'] = 'block must be a positive integer'

            if validBlock:
                for i in range(0, len(providerApis)):
                    data = providerApis[i].getBlock(self.blockHeight)
                    if 'success' in data and data['success'] == 1:
                        response = data
                        response['provider'] = providerNames[i]
                        break

                logProviderFailures(i)

                if response['success'] == 0:
                    response['error'] = 'All data providers failed'

        self.response.write(json.dumps(response))




class LatestBlock(webapp2.RequestHandler):
    def get(self):
        response = {'success': 0}
        for i in range(0, len(providerApis)):
            data = providerApis[i].getLatestBlock()
            if 'success' in data and data['success'] == 1:
                response = data
                response['provider'] = providerNames[i]
                break

        logProviderFailures(i)

        if response['success'] == 0:
            response['error'] = 'All data providers failed'

        self.response.write(json.dumps(response))


class PrimeInputAddress(webapp2.RequestHandler):
    def get(self):
        response = {'success': 0}
        self.txid = ''
        if self.request.get('txid') != '':
            self.txid = self.request.get('txid')

        if validTxid(self.txid):
            for i in range(0, len(providerApis)):
                data = providerApis[i].getPrimeInputAddress(self.txid)
                if 'success' in data and data['success'] == 1:
                    response = data
                    response['provider'] = providerNames[i]
                    break

            logProviderFailures(i)

            if response['success'] == 0:
                response['error'] = 'All data providers failed'

        else:
            logging.error("Invalid txid: "+ self.txid)
            response['error'] = "Invalid txid: "+ self.txid


        self.response.write(json.dumps(response))





class Transactions(webapp2.RequestHandler):
    def get(self):
        response = {'success': 0}
        self.address = ''
        if self.request.get('address') != '':
            self.address = self.request.get('address')

        if validAddress(self.address):
            for i in range(0, len(providerApis)):
                data = providerApis[i].getTXS(self.address)
                if 'success' in data and data['success'] == 1:
                    response['success'] = 1
                    response['TXS'] = self.TXS2JSON(data['TXS'], self.address)
                    response['provider'] = providerNames[i]
                    break

            logProviderFailures(i)

            if response['success'] == 0:
                response['error'] = 'All data providers failed'

        else:
            logging.error('Invalid address: ' + self.address)
            response['error'] = 'Invalid address: ' + self.address

        self.response.write(json.dumps(response))

    def TXS2JSON(self, TXS, address):
        jsonObj = []
        for i in range(0, len(TXS)):
            tx = TXS[i]
            jsonObj.append(tx.toDict(address))
        return jsonObj



class mainPage(webapp2.RequestHandler):
    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')
        template_values = {
            'Title': 'Blockchaindata',
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


class Documentation(webapp2.RequestHandler):
    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')

        template_values = {
            'Title': 'Blockchaindata documentation',
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
    ('/', mainPage),
    ('/documentation', Documentation),
    ('/transactions', Transactions),
    ('/utxos', UTXOs),
    ('/primeInputAddress', PrimeInputAddress),
    ('/latestBlock', LatestBlock),
    ('/block', Block),
    ('/balances', Balances),
], debug=True)

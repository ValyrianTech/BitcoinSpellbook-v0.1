import os
import jinja2
import webapp2
import urllib2
import json
import re
import includes
import hashlib

from google.appengine.ext import ndb
from google.appengine.api import urlfetch

from decimal import *

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

def getOptions(address, options, cost):
    optionsDict = {}
    for i in range(0, len(options)):
        option = {}
        option['description'] = options[i]
        option['amount'] = cost + i
        option['QR'] = "http://www.btcfrog.com/qr/bitcoinPNG.php?address=" + str(address) + "&amount=" + str(option['amount']/1e8) + "&error=H"
        if i%2 == 0:
            option['row'] = 'Even'
        else:
            option['row'] = 'Odd'

        optionsDict[i] = option

    return sorted(optionsDict.iteritems())

def getProposalHash(address, proposal, options):
    proposalHash = hashlib.sha256(address + proposal + options).hexdigest()
    return proposalHash


class Proposal(webapp2.RequestHandler):
    def get(self):
        error = ''
        self.address = ''
        self.resultsURL = '/results?'
        if self.request.get('address') != '':
            address = self.request.get('address')
            if validAddress(address):
                self.address = address
                self.resultsURL += 'proposalAddress=' + self.address
            else:
                error = "Invalid address: " + address

        self.proposal = ''
        if self.request.get('proposal') != '':
            self.proposal = self.request.get('proposal')
            self.resultsURL += '&proposal=' + self.proposal

        self.options = []
        strOptions = ''
        if self.request.get('options') != '':
            strOptions = self.request.get('options')
            self.options = strOptions.split('|')
            self.resultsURL += '&options=' + self.request.get('options')

        self.cost = 50000 #default cost to cast a vote in Satoshis
        if self.request.get('cost') != '':
            try:
                self.cost = int(self.request.get('cost'))
                self.resultsURL += '&cost=' + str(self.cost)
            except ValueError:
                error = "cost must be a positive integer"
        if self.cost <= 0:
            error = "cost must be a positive integer"


        self.digits = 1
        if self.request.get('digits') != '':
            try:
                self.digits = int(self.request.get('digits'))
                self.resultsURL += '&digits=' + str(self.digits)
            except ValueError:
                error = "Digits must be a positive integer"
        if self.digits <= 0:
            error = "Digits must be a positive integer"


        self.weights = 'Value'
        if self.request.get('weights') in ["Equal", "Value", "SIL", "LBL", "LRL", "LSL"]:
            self.weights = self.request.get('weights')
        self.resultsURL += '&weights=' + self.weights

        self.registrationAddress = ''
        if self.request.get('regAddress') != '':
            regAddress = self.request.get('regAddress')
            if validAddress(regAddress):
                self.registrationAddress = regAddress
                self.resultsURL += '&regAddress=' + self.registrationAddress

        self.registrationXPUB = ''
        if self.request.get('regXPUB') != '':
            regXPUB = self.request.get('regXPUB')
            if validXPUB(regXPUB):
                self.registrationXPUB = self.request.get('regXPUB')
                self.resultsURL += '&regXPUB=' + self.registrationXPUB

        self.registrationBlock = 0
        if self.request.get('regBlock') != '':
            try:
                self.registrationBlock = int(self.request.get('regBlock'))
                self.resultsURL += '&regBlock=' + str(self.registrationBlock)
            except ValueError:
                error = "regBlock must be a positive integer"
        if self.registrationBlock < 0:
            error = "regBlock must be a positive integer"


        rows = {}
        amounts = {}
        for i in range(0, len(self.options)):
            amounts[self.options[i]] = (self.cost + i)/1e8
            if i%2 == 0:
                rows[self.options[i]] = 'Even'
            else:
                rows[self.options[i]] = 'Odd'

        proposalHash = getProposalHash(self.address, self.proposal, strOptions)

        if self.request.get('format') == 'json' and error == '':
            proposal = {}
            proposal['address'] = self.address
            proposal['proposal'] = self.proposal
            proposal['options'] = getOptions(self.address, self.options, self.cost)
            proposal['cost'] = self.cost
            proposal['digits'] = self.digits
            if self.weights != '':
                proposal['weights'] = self.weights
            if self.registrationAddress != '':
                proposal['regAddress'] = self.registrationAddress
            if self.registrationXPUB != '':
                proposal['regXPUB'] = self.registrationXPUB
            if self.registrationBlock != 0:
                proposal['regBlock'] = self.registrationBlock

            proposal['proposalHash'] = proposalHash

            self.response.write(json.dumps({'success': 1, 'proposal': proposal}))

        elif self.request.get('format') == 'json' and error != '':
            self.response.write(json.dumps({'success': 0, 'error': error}))

        else:
            parameters = Parameters.get_or_insert('DefaultConfig')
            template_values = {
                'Title': 'Proposal',
                'address': self.address,
                'proposal': self.proposal,
                'proposalHash': proposalHash,
                'cost': self.cost,
                'digits': self.digits,
                'options': getOptions(self.address, self.options, self.cost),
                'weights': self.weights,
                'regAddress': self.registrationAddress,
                'regXPUB': self.registrationXPUB,
                'regBlock': self.registrationBlock,
                'error': error,
                'resultsURL': self.resultsURL,

                'nOptions': len(self.options),
                'amounts': amounts,
                'rows': rows,

                'cssHTML': includes.get_CssHTML(),
                'metaHTML': includes.get_MetaHTML(),
                'scriptsHTML': includes.get_ScriptsHTML(),
                'navigationHTML': includes.get_NavigationHTML(Spellbook(parameters)),
                'logoHTML': includes.get_LogoHTML(),
                'footerHTML': includes.get_FooterHTML(),
                'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),

            }

            template = JINJA_ENVIRONMENT.get_template('proposal.html')

            self.response.write(template.render(template_values))







class MainHandler(webapp2.RequestHandler):
    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')
        error = ''

        self.proposalAddress = ''
        if self.request.get('proposalAddress') != '':
            address = self.request.get('proposalAddress')
            if validAddress(address):
                self.proposalAddress = address
            else:
                error = "Invalid address: " + address

        url = parameters.blockchaindataURL + '/latestBlock'
        data = {}
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


        proposalBlock = 0
        if self.request.get('proposalBlock') != '':
            try:
                proposalBlock = int(self.request.get('proposalBlock'))
            except ValueError:
                error = "proposalBlock must be a positive integer"
        else:
            proposalBlock = latestBlock


        weights = ''
        if self.request.get('weights') in ['Value', 'Equal', 'SIL', 'LBL', 'LRL', 'LSL']:
            weights = self.request.get('weights')
        elif self.request.get('weights') != '':
            error = 'Incorrect weights'

        self.registrationAddress = ''
        if self.request.get('regAddress') != '':
            regAddress = self.request.get('regAddress')
            if validAddress(regAddress):
                self.registrationAddress = self.request.get('regAddress')
            else:
                error = "Invalid regAddress: " + regAddress

        self.registrationBlockHeight = latestBlock
        if self.request.get('regBlock') != '':
            try:
                self.registrationBlockHeight = int(self.request.get('regBlock'))
            except ValueError:
                error = "regBlock must be a positive integer"
        if self.registrationBlockHeight < 0:
            error = "regBlock must be a positive integer"


        self.registrationXPUB = ''
        if self.request.get('regXPUB') != '':
            regXPUB = self.request.get('regXPUB')
            if validXPUB(regXPUB):
                self.registrationXPUB = regXPUB
            else:
                error = "Invalid regXPUB: " + regXPUB

        self.weightValues = []
        if weights == 'SIL' and self.registrationAddress != '' and self.registrationBlockHeight != 0:

            url = parameters.simplifiedInputsListURL + '/SIL?format=json&address=' + self.registrationAddress + '&block=' + str(self.registrationBlockHeight)
            data = {}
            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
            except:
                error = 'Unable to retrieve SIL'

            if 'success' in data and data['success'] == 1:
                self.weightValues = data['SIL']

        elif weights in ['LBL', 'LRL', 'LSL'] and self.registrationAddress != '' and self.registrationBlockHeight != 0 and self.registrationXPUB != '':
            url = parameters.blocklinkerURL + '/LinkedList?format=json&address=' + self.registrationAddress + '&block=' + str(self.registrationBlockHeight) + '&xpub=' + self.registrationXPUB + '&metric=' + weights
            data = {}
            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
            except:
                error = 'Unable to retrieve Linked values'

            if 'success' in data and data['success'] == 1:
                if weights == 'LBL':
                    self.weightValues = data['LBL']
                elif weights == 'LRL':
                    self.weightValues = data['LRL']
                elif weights == 'LSL':
                    self.weightValues = data['LSL']


        digits = 1
        if self.request.get('digits') != '':
            try:
                digits = int(self.request.get('digits'))
            except ValueError:
                error = "Digits must be a positive integer"
        if digits <= 0:
            error = "Digits must be a positive integer"
            digits = 1


        self.proposal = ''
        if self.request.get('proposal') != '':
            self.proposal = self.request.get('proposal')

        self.options = []
        self.optionsDict = {}
        strOptions = ''
        if self.request.get('options') != '':
            strOptions = self.request.get('options')
            self.options = strOptions.split('|')
            i = 0
            for option in self.options:
                self.optionsDict[str(i)] = option
                i += 1




        TXS = []
        if self.proposalAddress != '':
            url = parameters.blockchaindataURL + '/transactions?format=json&address=' + self.proposalAddress + '&block=' + str(proposalBlock)
            data = {}
            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
            except:
                data = {}

            if 'success' in data and data['success'] == 1:
                TXS = data['TXS']
            else:
                error = 'Unable to retrieve transactions'

        votes = self.convertTXs2Votes(TXS, proposalBlock, digits)
        nVotes = len(votes)
        results = self.calcResults(votes, weights)
        nResults = len(results)

        rows = {}
        toggle = 'Odd'
        for option in sorted(results):
            rows[option] = toggle

            if toggle == 'Odd':
                toggle = 'Even'
            elif toggle == 'Even':
                toggle = 'Odd'

        proposalHash = getProposalHash(self.proposalAddress, self.proposal, strOptions)

        if self.request.get('format') == 'json' and error == '':
            response = {'success': 1}
            response['results'] = results
            response['options'] = self.optionsDict

            response['digits'] = digits
            response['block'] = proposalBlock
            if self.proposal != '':
                response['proposal'] = self.proposal
            if self.proposalAddress != '':
                response['proposalAddress'] = self.proposalAddress
            if self.registrationAddress != '':
                response['regAddress'] = self.registrationAddress
            if self.registrationBlockHeight != '':
                response['regBlock'] = self.registrationBlockHeight
            if self.registrationXPUB != '':
                response['regXPUB'] = self.registrationXPUB
            if weights != '':
                response['weights'] = weights

            response['proposalHash'] = proposalHash

            self.response.write(json.dumps(response))

        elif self.request.get('format') == 'json' and error != '':
            self.response.write(json.dumps({'success': 0, 'error': error}))

        else:
            parameters = Parameters.get_or_insert('DefaultConfig')
            template_values = {
                'Title': 'Bitvoter',
                'proposalAddress': self.proposalAddress,
                'proposalBlock': proposalBlock,
                'regAddress': self.registrationAddress,
                'regBlock': self.registrationBlockHeight,
                'regXPUB': self.registrationXPUB,

                'proposal': self.proposal,
                'options': self.optionsDict,
                'strOptions': strOptions,

                'latestBlock': latestBlock,
                'votes': votes,
                'nVotes': nVotes,
                'optionIDs': sorted(results , key=lambda x: int(x)),
                'results': results,
                'nResults': nResults,
                'weights': weights,
                'digits': digits,
                'evenRow': 0,
                'error': error,
                'rows': rows,

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

    def convertTXs2Votes(self, TXs, blockheight, significantDigits=1):
        votes = {}
        for i in range(0, len(TXs)):
            if TXs[i]['blockheight'] <= blockheight:
                voter = TXs[i]['primeInputAddress']
                vote = str(TXs[i]['receivedValue'])[-significantDigits:]
                value = TXs[i]['receivedValue'] - int(vote)

                if voter in votes:
                    votes[voter]['lastVote'] = vote
                    votes[voter]['value'] += value
                else:
                    votes[voter] = {'lastVote': vote, 'value': value}


        return votes


    def calcResults(self, votes, weights):
        results = {}
        for voter in votes:

            if int(votes[voter]['lastVote']) == 0:
                option = "0"
            else:
                option = str(votes[voter]['lastVote']).lstrip("0")

            if weights == 'Value':
                if option in results:
                    results[option] += votes[voter]['value']
                else:
                    results[option] = votes[voter]['value']

            elif weights == 'Equal':
                if option in results:
                    results[option] += 1
                else:
                    results[option] = 1

            elif weights in ['SIL', 'LBL', 'LRL', 'LSL']:
                value = 0
                for tx_input in self.weightValues:
                    if tx_input[0] == voter:
                        value = tx_input[1]
                        break

                if option in results:
                    results[option] += value
                else:
                    results[option] = value

        return results


class Documentation(webapp2.RequestHandler):
    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')

        template_values = {
            'Title': 'Bitvoter documentation',
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
    ('/proposal', Proposal),
    ('/results', MainHandler),
], debug=True)

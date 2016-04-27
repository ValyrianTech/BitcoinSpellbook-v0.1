__author__ = 'Wouter'
import urllib2
import json
import urllib


class BlockchainData():
    def __init__(self, url):
        self.url = url


    def UTXOs(self, addresses=[]):
        parameters = {}
        parameters['format'] = 'json'

        if addresses != []:
            strAddresses = ""
            for address in addresses:
                strAddresses += address + "|"

            strAddresses = strAddresses[:-1]
            parameters['addresses'] = strAddresses


        utxos = {}

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/utxos?" + queryString

        data = []
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve UTXOs")

        if 'success' in data and data['success'] == 1:
            utxos = data['UTXOs']

        return utxos

    def balances(self, addresses=[]):
        parameters = {}
        parameters['format'] = 'json'

        if addresses != []:
            strAddresses = ""
            for address in addresses:
                strAddresses += address + "|"

            strAddresses = strAddresses[:-1]
            parameters['addresses'] = strAddresses

        balances = {}

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/balances?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve balances")

        if 'success' in data and data['success'] == 1:
            balances = data['balances']

        return balances

    def transactions(self, address):
        parameters = {}
        parameters['format'] = 'json'
        parameters['address'] = address

        txs = []

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/transactions?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve TXS")

        if 'success' in data and data['success'] == 1:
            txs = data['TXS']

        return txs

    def block(self, height):
        parameters = {}
        parameters['format'] = 'json'
        parameters['block'] = str(height)

        block = {}

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/block?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve block")

        if 'success' in data and data['success'] == 1:
            block['merkleroot'] = data['block']['merkleroot']
            block['hash'] = data['block']['hash']
            block['height'] = data['block']['height']
            block['time'] = data['block']['time']
            block['size'] = data['block']['size']

        return block

    def latestBlock(self):
        parameters = {}
        parameters['format'] = 'json'

        block = {}

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/latestBlock?" + queryString

        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve latest block")

        if 'success' in data and data['success'] == 1:
            block['merkleroot'] = data['latestBlock']['merkleroot']
            block['hash'] = data['latestBlock']['hash']
            block['height'] = data['latestBlock']['height']
            block['time'] = data['latestBlock']['time']
            block['size'] = data['latestBlock']['size']

        return block


    def primeInputAddress(self, txid):
        parameters = {}
        parameters['format'] = 'json'
        parameters['txid'] = txid

        primeInputAddress = ''

        queryString  = urllib.urlencode(parameters)
        url = self.url +"/primeInputAddress?" + queryString
        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            raise Exception("Unable to retrieve prime input address")

        if 'success' in data and data['success'] == 1:
            primeInputAddress = data['PrimeInputAddress']

        return primeInputAddress

__author__ = 'Wouter'

import urllib2
import json

from TX import TX

from pprint import pprint
from decimal import *
import logging

API_URL = 'https://blockexplorer.com/api/'
#API_URL = 'https://insight.bitpay.com/api/' #don't use

class API:
    def __init__(self, url=API_URL):
        self.url = url
        pass

    def getTXS(self, addresses):
        response = {'success': 0}
        txs = []
        LIMIT = 100 #number of tx given by insight is 100

        latestBlockHeight = -1
        try:
            latestBlock = self.getLatestBlock()
            latestBlockHeight = latestBlock['latestBlock']['height']
        except:
            logging.warning('Insight: Unable to retrieve latest block')
            response = {'success': 0, 'error': 'Unable to retrieve latest block'}

        url = self.url + 'addrs/' + addresses + '/txs'
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            logging.warning('Insight: Unable to retrieve transactions')
            response = {'success': 0, 'error': 'Unable to retrieve transactions'}

        if 'totalItems' in data:
            transactions = data['items']
            nTx = data['totalItems']


            if nTx > LIMIT:
                for i in range(1, int(nTx/LIMIT)+1):
                    url =  self.url + 'addrs/' + addresses + '/txs?from=' + str(LIMIT*i) + '&to=' + str(LIMIT*(i+1))
                    try:
                        ret = urllib2.urlopen(urllib2.Request(url))
                        data = json.loads(ret.read())
                        transactions += data['items']
                    except:
                        logging.warning('Insight: Unable to retrieve next page')
                        response = {'success': 0, 'error': 'Unable to retrieve next page'}

        for transaction in transactions:

            tx = TX()
            tx.txid = transaction['txid']
            tx.confirmations = transaction['confirmations']
            tx.blockHeight = latestBlockHeight - tx.confirmations + 1
            for input in transaction['vin']:
                tx_in = {}
                tx_in['address'] = input['addr']
                tx_in['value'] = input['valueSat']
                tx.inputs.append(tx_in)

            for out in transaction['vout']:
                tx_out = {}
                tx_out['address'] = out['scriptPubKey']['addresses'][0]
                tx_out['value'] = int(Decimal(out['value']) * Decimal(1e8))
                if 'spentTxId' in out:
                    tx_out['spent'] = True
                else:
                    tx_out['spent'] = False


                tx.outputs.append(tx_out)

            txs.insert(0, tx)

        if nTx != len(txs):
            logging.warning('Insight: Warning: not all transactions are retreived! ' + str(len(txs)) + ' of ' +  str(nTx))
            response = {'success': 0, 'error': 'Warning: not all transactions are retrieved! ' + str(len(txs)) + ' of ' +  str(nTx)}
        else:
            response = {'success': 1, 'TXS': txs}

        return response

    def getLatestBlock(self):
        response = {'success': 0}
        latestBlock = {}
        data = {}
        url = self.url + 'status?q=getInfo'
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            logging.warning('Insight: Unable to retrieve latest block')
            response = {'success': 0, 'error': 'Unable to retrieve latest block'}

        if 'info' in data:
            latestBlock['height'] = data['info']['blocks']
            data = {}
            try:
                data = self.getBlock(latestBlock['height'])
            except:
                logging.warning('Insight: Unable to retrieve block')
                response = {'success': 0, 'error': 'Unable to retrieve block'}

            if 'success' in data and data['success'] == 1:
                latestBlock['hash'] = data['block']['hash']
                latestBlock['time'] = data['block']['time']
                latestBlock['merkleroot'] = data['block']['merkleroot']
                latestBlock['size'] = data['block']['size']
            response = {'success': 1, 'latestBlock': latestBlock}

        return response

    def getBlock(self, height):
        response = {'success': 0}
        block = {}
        data = {}
        url = self.url +   'block-index/' + str(height)
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            logging.warning('Insight: unable to retrieve block ' + str(height))
            response = {'success': 0, 'error': 'unable to retrieve block ' + str(height)}


        if 'blockHash' in data:
            block['height'] = id
            block['hash'] = data['blockHash']

            url = self.url +  'block/' + block['hash']
            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
            except:
                logging.warning('Insight: Unable to retrieve block ' + block['hash'])
                response = {'success': 0, 'error': 'Unable to retrieve block ' + block['hash']}

            if 'hash' in data and data['hash'] == block['hash']:
                block['time'] = data['time']
                block['merkleroot'] = data['merkleroot']
                block['size'] = data['size']
            response = {'success': 1, 'block': block}

        return response

    def getBalance(self, addresses):
        response = {'success': 0}

        if len(addresses.split("|")) > 10:
            response = {'success': 0, 'error': 'Max 10 addresses, api function for multiple address lookup not available at ' + self.url}
        else:
            balances = {}
            for address in addresses.split("|"):
                data = {}

                url = self.url + 'addr/' + address
                try:
                    ret = urllib2.urlopen(urllib2.Request(url))
                    data = json.loads(ret.read())
                except:
                    logging.warning('Insight: Unable to retrieve data for addresses ' + addresses)
                    response = {'success': 0, 'error': 'Unable to retrieve data for addresses ' + addresses}

                if 'addrStr' in data and data['addrStr'] == address:
                    balances[data['addrStr']] = {}
                    balances[data['addrStr']]['balance'] = data['balanceSat']

                    txs = self.getTXS(address)
                    received = 0
                    sent = 0
                    for tx in txs['TXS']:
                        if tx.receivingTX(address) == True and tx.confirmations > 0:
                            received += tx.receivedValue(address)

                        elif tx.sendingTX(address) == True and tx.confirmations > 0:
                            sent += tx.sentValue(address)


                    balances[data['addrStr']]['received'] = received
                    balances[data['addrStr']]['sent'] = sent
                    response = {'success': 1, 'balances': balances}

        return response


    def getPrimeInputAddress(self, txid):
        response = {'success': 0}
        url = self.url + 'tx/' + str(txid)
        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            logging.warning('Insight: Unable to retrieve prime input address of tx ' + txid)
            response = {'success': 0, 'error': 'Unable to retrieve prime input address of tx ' + txid}


        tx_inputs = []
        if 'txid' in data and data['txid'] == txid:
            tx_inputs = data['vin']

            inputAddresses = []
            for i in range(0, len(tx_inputs)):
                inputAddresses.append(tx_inputs[i]['addr'])

            primeInputAddress = []
            if len(inputAddresses) > 0:
                primeInputAddress = sorted(inputAddresses)[0]

            response = {'success': 1, 'PrimeInputAddress': primeInputAddress}

        return response

    #Multiple bitcoin addresses, separated by ","
    def getUTXOs(self, addresses, confirmations=3):
        response = {'success': 0}
        addresses = addresses.replace('|', ',')

        latestBlockHeight = 0
        try:
            latestBlock = self.getLatestBlock()
            latestBlockHeight = latestBlock['latestBlock']['height']
        except:
            logging.warning('Insight: Unable to retrieve latest block')
            response = {'success': 0, 'error': 'Unable to retrieve latest block'}

        UTXOs = []
        url = self.url +  'addrs/' + addresses + '/utxo'
        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            logging.warning('Insight: Unable to retrieve utxos')
            response = {'success': 0, 'error': 'Unable to retrieve utxos'}

        for i in range(0, len(data)):
            utxo = {}
            utxo['address'] = data[i]['address']

            url = self.url +  'tx/' + data[i]['txid']
            tx = {}
            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                tx = json.loads(ret.read())
            except:
                logging.warning('Insight: Unable to retrieve tx' + data[i]['txid'])
                response = {'success': 0, 'error': 'Unable to retrieve tx' + data[i]['txid']}

            if 'txid' in tx and tx['txid'] == data[i]['txid']:
                utxo['confirmations'] = int(tx['confirmations'])
                utxo['block_height'] = latestBlockHeight - utxo['confirmations'] +1

            utxo['output'] = data[i]['txid'] + ":" + str(data[i]['vout'])
            utxo['value'] = int(data[i]['amount'] * 1e8)

            if utxo['confirmations'] >= confirmations:
                UTXOs.append(utxo)

            response = {'success': 1, 'UTXOs': UTXOs}
        return response

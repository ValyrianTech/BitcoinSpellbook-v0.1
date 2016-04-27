__author__ = 'Wouter'

import urllib2
import json
import logging
from TX import TX

from pprint import pprint

API_VERSION = 'v1'

class API:
    def __init__(self, key='', secret=''):
        self.key = key
        self.secret = secret

    def getTXS(self, address):
        response = {'success': 0}
        LIMIT = 50 #max number of tx given by blockchain.info is 50

        latestBlockHeight = -1
        try:
            latestBlockHeight = self.getLatestBlock()['latestBlock']['height']
        except:
            logging.warning('Blockchain.info: unable to retrieve latest block')
            response = {'success': 0, 'error': 'unable to retrieve latest block'}

        url = 'https://blockchain.info/address/' + address + '?format=json&limit=' + str(LIMIT)
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            data = {}

        transactions = data['txs']
        nTx = data['n_tx']

        if 'n_tx' in data:
            n_tx = data['n_tx']
            if n_tx > LIMIT:
                for i in range(1, int(n_tx/LIMIT)+1):
                    url = 'https://blockchain.info/address/' + address + '?format=json&limit=' + str(LIMIT) + '&offset=' + str(LIMIT*i)
                    try:
                        ret = urllib2.urlopen(urllib2.Request(url))
                        data = json.loads(ret.read())
                        transactions += data['txs']
                    except:
                        logging.warning('Blockchain.info: unable to retrieve next page')
                        response = {'success': 0, 'error': 'unable to retrieve next page '}

        txs = []
        for transaction in transactions:

            tx = TX()
            tx.txid = transaction['hash']

            if 'block_height' in transaction:
                tx.blockHeight = transaction['block_height']
                tx.confirmations = (latestBlockHeight - tx.blockHeight) +1
            else:
                tx.blockHeight = None
                tx.confirmations = 0

            for input in transaction['inputs']:
                tx_in = {}
                tx_in['address'] = input['prev_out']['addr']
                tx_in['value'] = input['prev_out']['value']
                tx.inputs.append(tx_in)

            for out in transaction['out']:
                tx_out = {}
                tx_out['address'] = out['addr']
                tx_out['value'] = out['value']
                tx_out['spent'] = out['spent']
                tx.outputs.append(tx_out)

            txs.insert(0, tx)

        if nTx != len(txs):
            logging.warning('Blockchain.info: Warning: not all transactions are retrieved! ' + str(len(txs)) + ' of ' +  str(nTx))
            response = {'success': 0, 'error': 'Not all transactions are retrieved ' + str(len(txs)) + ' of ' +  str(nTx)}
        else:
            response = {'success': 1, 'TXS': txs}

        return response

    def getLatestBlock(self):
        response = {'success': 0}
        latestBlock = {}
        data = {}
        url = 'https://blockchain.info/nl/latestblock'
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            logging.warning('Blockchain.info: unable to retrieve latest block')
            response = {'success': 0, 'error': 'unable to retrieve latest block'}

        if 'height' in data:
            latestBlock['height'] = data['height']
            latestBlock['hash'] = data['hash']
            latestBlock['time'] = data['time']

            url = 'https://blockchain.info/nl/rawblock/' + latestBlock['hash']
            data = {}
            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
            except:
                logging.warning('Blockchain.info: unable to retrieve block ' + str(latestBlock['height']))
                response = {'success': 0, 'error': 'unable to retrieve block ' + str(latestBlock['height'])}

            if 'hash' in data and data['hash'] == latestBlock['hash']:
                latestBlock['merkleroot'] = data['mrkl_root']
                latestBlock['size'] = data['size']

            response = {'success': 1, 'latestBlock': latestBlock}

        return response

    def getBlock(self, height):
        response = {'success': 0}
        block = {}
        data = {}
        url = 'https://blockchain.info/nl/block-height/' + str(height) + '?format=json'
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            logging.warning('Blockchain.info: unable to retrieve block ' + str(height))
            response = {'success': 0, 'error': 'unable to retrieve block ' + str(height)}

        if 'blocks' in data:
            blocks = data['blocks']

            for i in range(0, len(blocks)):
                if blocks[i]['main_chain'] == True and blocks[i]['height'] == height:
                    block['height'] = blocks[i]['height']
                    block['hash'] = blocks[i]['hash']
                    block['time'] = blocks[i]['time']
                    block['merkleroot'] = blocks[i]['mrkl_root']
                    block['size'] = blocks[i]['size']

            response = {'success': 1, 'block': block}

        return response

    #(Multiple addresses divided by |)
    def getBalance(self, addresses):
        response = {'success': 0}
        data = {}
        balances = {}
        url = 'https://blockchain.info/nl/multiaddr?active=' + addresses
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            logging.warning('Blockchain.info: unable to retrieve data for addresses ' + addresses)
            response = {'success': 0, 'error': 'unable to retrieve data for addresses ' + addresses}



        if 'addresses' in data:
            for i in range(0, len(data['addresses'])):
                address = data['addresses'][i]
                balances[address['address']] = {}
                balances[address['address']]['balance'] = address['final_balance']
                balances[address['address']]['received'] = address['total_received']
                balances[address['address']]['sent'] = address['total_sent']

            response = {'success': 1, 'balances': balances}

        return response

    def getPrimeInputAddress(self, txid):
        url = 'https://blockchain.info/nl/rawtx/' + str(txid)
        data = {}
        response = {'success': 0}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            logging.warning('Blockchain.info: unable to retrieve prime input address of tx ' + txid)
            response = {'success': 0, 'error': 'unable to retrieve prime input address of tx ' + txid}


        tx_inputs = []
        if 'hash' in data and data['hash'] == txid:
            tx_inputs = data['inputs']

            inputAddresses = []
            for i in range(0, len(tx_inputs)):
                inputAddresses.append(tx_inputs[i]['prev_out']['addr'])

            primeInputAddress = []
            if len(inputAddresses) > 0:
                primeInputAddress = sorted(inputAddresses)[0]

            response = {'success': 1, 'PrimeInputAddress': primeInputAddress}

        return response

    #Multiple bitcoin addresses, separated by "|"
    def getUTXOs(self, addresses, confirmations=3):
        response = {'success': 0}
        UTXOs = []
        url = 'https://blockchain.info/nl/unspent?active=' + addresses
        data = {}
        try:
            ret = urllib2.urlopen(urllib2.Request(url))
            data = json.loads(ret.read())
        except:
            logging.warning('Blockchain.info: unable to retrieve utxos')
            response = {'success': 0, 'error': 'unable to retrieve utxos'}


        if 'unspent_outputs' in data:
            for i in range(0, len(data['unspent_outputs'])):
                utxo = {}

                utxo['confirmations'] = int(data['unspent_outputs'][i]['confirmations'])
                utxo['output'] = data['unspent_outputs'][i]['tx_hash_big_endian'] + ":" + str(data['unspent_outputs'][i]['tx_output_n'])
                utxo['value'] = data['unspent_outputs'][i]['value']

                if utxo['confirmations'] >= confirmations:
                    UTXOs.append(utxo)

                url = 'https://blockchain.info/nl/rawtx/' + data['unspent_outputs'][i]['tx_hash_big_endian']
                tx = {}
                try:
                    ret = urllib2.urlopen(urllib2.Request(url))
                    tx = json.loads(ret.read())
                except:
                    logging.warning('Blockchain.info: unable to retrieve utxos')
                    response = {'success': 0, 'error': 'unable to retrieve utxos'}

                if 'hash' in tx and tx['hash'] == data['unspent_outputs'][i]['tx_hash_big_endian']:
                    utxo['block_height'] = tx['block_height']
                    for tx_output in tx['out']:
                        if tx_output['n'] == data['unspent_outputs'][i]['tx_output_n']:
                            utxo['address'] = tx_output['addr']



            response = {'success': 1, 'UTXOs': UTXOs}
        return response
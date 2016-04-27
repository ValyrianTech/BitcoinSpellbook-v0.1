__author__ = 'Wouter Glorieux'

import bitcoin
import BIP44
import BlockchainDataWrapper
import SimplifiedInputsListWrapper
import BlocklinkerWrapper
import ProportionalRandomWrapper
import BitvoterWrapper
import HDForwarderWrapper
import DistributeBTCWrapper
import BitcoinWellsWrapper

from pprint import pprint
import sys

BLOCKCHAINDATA_URL = 'https://blockchaindata.appspot.com'
SIL_URL = 'https://simplifiedinputslist.appspot.com'
BLOCKLINKER_URL = 'https://blocklinker.appspot.com'
PROPORTIONALRANDOM_URL = 'https://proportionalrandom.appspot.com'
BITVOTER_URL = 'https://bitvoter.appspot.com'
HDFORWARDER_URL = 'https://hdforwarder.appspot.com'
DISTRIBUTEBTC_URL = 'https://distributebtc.appspot.com'
BITCOINWELLS_URL = 'https://bitcoinwells.appspot.com'

class BitcoinSpellbook():

    def __init__(self):
        self.address = ''

    def BlockchainData(self, url=BLOCKCHAINDATA_URL):
        return BlockchainDataWrapper.BlockchainData(url)

    def SIL(self, url=SIL_URL):
        return SimplifiedInputsListWrapper.SIL(url)

    def Blocklinker(self, url=BLOCKLINKER_URL):
        return BlocklinkerWrapper.Blocklinker(url)

    def HDForwarder(self, url=HDFORWARDER_URL):
        return HDForwarderWrapper.HDForwarder(url)

    def DistributeBTC(self, url=DISTRIBUTEBTC_URL):
        return DistributeBTCWrapper.DistributeBTC(url)

    def BitcoinWells(self, url=BITCOINWELLS_URL):
        return BitcoinWellsWrapper.BitcoinWells(url)

    def ProportionalRandom(self, url=PROPORTIONALRANDOM_URL):
        return ProportionalRandomWrapper.ProportionalRandom(url)

    def Bitvoter(self, url=BITVOTER_URL):
        return BitvoterWrapper.Bitvoter(url)

    def BIP44(self):
        return BIP44

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
            pprint("Warning: Fee incorrect! aborting transaction")
        else:
            allKeysPresent = True
            allInputsConfirmed = True
            for tx_input in UTXOs:
                if tx_input['address'] not in privkeys:
                    print 'not found:', tx_input['address']
                    allKeysPresent = False

                if tx_input['block_height'] == None:
                    allInputsConfirmed = False

            if allKeysPresent == True and allInputsConfirmed == True:
                tx = bitcoin.mktx(UTXOs, outputs)
                for i in range(0, len(UTXOs)):
                    tx = bitcoin.sign(tx, i, str(privkeys[UTXOs[i]['address']]))

                try:
                    bitcoin.pushtx(tx)
                    success = True
                except:
                    e = sys.exc_info()
                    print e
                    success = False

        return success

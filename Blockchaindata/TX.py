__author__ = 'Wouter'


class TX():
    def __init__(self):
        self.txid = ''
        self.inputs = []
        self.outputs = []
        self.blockHeight = 0
        self.confirmations = 0

    def printTX(self):
        print '\nblock ', str(self.blockHeight) , "(" + str(self.confirmations) + " confirmations)", self.txid
        print 'IN:', self.inputs
        print 'OUT:', self.outputs
        print 'primeInput:', self.primeInputAddress()

    def primeInputAddress(self):
        addresses = []
        for tx_input in self.inputs:
            addresses.append(tx_input['address'])

        return sorted(addresses)[0]


    def receivedValue(self, address):
        value = 0
        for output in self.outputs:
            if output['address'] == address:
                value += output['value']

        return value

    def receivingTX(self, address):
        received = True
        for tx_input in self.inputs:
            if tx_input['address'] == address:
                received = False

        return received


    def sentValue(self, address):
        value = 0
        for tx_input in self.inputs:
            if tx_input['address'] == address:
                value += tx_input['value']

        change = 0
        for tx_output in self.outputs:
            if tx_output['address'] == address:
                change += tx_output['value']

        return value-change

    def sendingTX(self, address):
        sending = False
        for tx_input in self.inputs:
            if tx_input['address'] == address:
                sending = True

        return sending



    def toDict(self, address):
        tx_dict = {}
        tx_dict["txid"] = self.txid
        tx_dict["primeInputAddress"] = self.primeInputAddress()
        tx_dict["inputs"] = self.inputs
        tx_dict["outputs"] = self.outputs
        tx_dict["blockheight"] = self.blockHeight
        tx_dict["confirmations"] = self.confirmations
        tx_dict["receiving"] = self.receivingTX(address)
        tx_dict["receivedValue"] = self.receivedValue(address)

        return tx_dict

def sortTXS(self, txs):
    blockTXS = {}
    for tx in txs:
        if tx.blockheight in blockTXS:
            blockTXS[tx.blockheight].append(tx)
        else:
            blockTXS[tx.blockheight] = [tx]

    sortedTXS = []
    for block in sorted(blockTXS):
        for tx in sorted(blockTXS[block], key= lambda x: x.txid):
            if self.receivingOnly == False or tx.receivingTX(self.address) == True:
                sortedTXS.append(tx)

    return sortedTXS
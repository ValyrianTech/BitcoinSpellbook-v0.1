__author__ = 'Wouter'
import bitcoin
from mnemonic import Mnemonic
from binascii import hexlify, unhexlify
import json
import urllib2
from pprint import pprint

HARDENED = 2**31

class Wallet():
    def __init__(self, mnemonic, passphrase="", account=0, n=100):
        self.mnemonic = mnemonic
        self.passphrase = passphrase
        self.account = account
        self.xpubKeys = getXPUBKeys(self.mnemonic, self.passphrase, account+1)
        self.xprivKeys = getXPRIVKeys(self.mnemonic, self.passphrase, account+1)

        self.n = n
        self.addresses = getAddressesFromXPUB(self.xpubKeys[account], self.n)
        self.changeAddresses = getChangeAddressesFromXPUB(self.xpubKeys[account], self.n)
        #showDetails(self.mnemonic, self.passphrase, 3)

    def scan(self):
        UnspentOutputs = {}
        bundleSize = 200
        k = 0
        for addressList in [self.addresses, self.changeAddresses]:
            i = 0
            while i < self.n:
                slice = addressList[i:i+bundleSize]

                url = 'https://blockchain.info/multiaddr?active=' + bundleAddresses(slice)
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())

                for j in range(0, len(data['addresses'])):
                    if data['addresses'][j]['final_balance'] > 0:
                        keyIndex = addressList.index(data['addresses'][j]['address'])
                        privKey = getPrivKey(self.xprivKeys[self.account], keyIndex, k)
                        UnspentOutputs[data['addresses'][j]['address']] = {'value': data['addresses'][j]['final_balance'], 'i': keyIndex, 'privkey': privKey[data['addresses'][j]['address']], 'change': k, "account": self.account}

                i = i + bundleSize

            k += 1

        pprint(UnspentOutputs)

        totalValue = 0
        for address in UnspentOutputs:
            totalValue += UnspentOutputs[address]['value']

        print 'Total value:', totalValue/1e8, 'BTC'

        return UnspentOutputs


    def sweep(self, toAddress):
        pass


def getAddressesFromXPUB(xpub, i=100):
    addressList = []
    pub0 = bitcoin.bip32_ckd(xpub, 0)

    for i in range (0, i):
        publicKey = bitcoin.bip32_ckd(pub0, i)
        hexKey = bitcoin.encode_pubkey(bitcoin.bip32_extract_key(publicKey), 'hex_compressed')
        address_fromPub =  bitcoin.pubtoaddr(hexKey)
        addressList.append(address_fromPub)

    return addressList


def getChangeAddressesFromXPUB(xpub, i=100):
    addressList = []
    pub0 = bitcoin.bip32_ckd(xpub, 1)

    for i in range (0, i):
        publicKey = bitcoin.bip32_ckd(pub0, i)
        hexKey = bitcoin.encode_pubkey(bitcoin.bip32_extract_key(publicKey), 'hex_compressed')
        address_fromPub =  bitcoin.pubtoaddr(hexKey)
        addressList.append(address_fromPub)

    return addressList


def getXPRIVKeys(mnemonic, passphrase="", i=1):

    myMnemonic = mnemonic
    passphrase = passphrase

    mnemo = Mnemonic('english')
    seed = hexlify(mnemo.to_seed(myMnemonic, passphrase=passphrase))

    priv = bitcoin.bip32_master_key(unhexlify(seed))

    account = 0
    #derivedPrivateKey = bitcoin.bip32_ckd(bitcoin.bip32_ckd(bitcoin.bip32_ckd(priv, 44+HARDENED), HARDENED), HARDENED+account)

    xprivs = []
    for i in range(0, i):
        derivedPrivateKey = bitcoin.bip32_ckd(bitcoin.bip32_ckd(bitcoin.bip32_ckd(priv, 44+HARDENED), HARDENED), HARDENED+i)
        xprivs.append(derivedPrivateKey)

    return xprivs

def getPrivKey(xpriv, i, k=0):
    privkeys = {}
    priv0 = bitcoin.bip32_ckd(xpriv, k)

    privateKey = bitcoin.bip32_ckd(priv0, i)
    wifKey = bitcoin.encode_privkey(bitcoin.bip32_extract_key(privateKey), 'wif_compressed')
    address_fromPriv =  bitcoin.privtoaddr(wifKey)
    privkeys[address_fromPriv] = wifKey

    return privkeys

def getXPUBKeys(mnemonic, passphrase="", i=1):

    myMnemonic = mnemonic
    passphrase = passphrase

    mnemo = Mnemonic('english')
    seed = hexlify(mnemo.to_seed(myMnemonic, passphrase=passphrase))

    priv = bitcoin.bip32_master_key(unhexlify(seed))

    account = 0
    #derivedPrivateKey = bitcoin.bip32_ckd(bitcoin.bip32_ckd(bitcoin.bip32_ckd(priv, 44+HARDENED), HARDENED), HARDENED+account)

    xpubs = []
    for i in range(0, i):
        derivedPrivateKey = bitcoin.bip32_ckd(bitcoin.bip32_ckd(bitcoin.bip32_ckd(priv, 44+HARDENED), HARDENED), HARDENED+i)
        xpub = bitcoin.bip32_privtopub(derivedPrivateKey)
        xpubs.append(xpub)

    return xpubs

def showDetails(mnemonic, passphrase="", i=1):

    myMnemonic = mnemonic
    passphrase = passphrase


    mnemo = Mnemonic('english')
    seed = hexlify(mnemo.to_seed(myMnemonic, passphrase=passphrase))
    print 'Seed:\t\t\t\t', seed

    priv = bitcoin.bip32_master_key(unhexlify(seed))
    print 'Xpriv:\t\t\t\t', priv

    key = bitcoin.encode_privkey(bitcoin.bip32_extract_key(priv), 'wif_compressed')
    print 'Key:\t\t\t\t', key


    pub = bitcoin.bip32_privtopub(priv)
    print 'Derived public key:\t', pub
    pubHex = bitcoin.bip32_extract_key(pub)
    print 'public key (hex):\t', pubHex
    print 'Master Key address:\t', bitcoin.pubtoaddr(pubHex)


    print ""
    print "TREZOR Keys:"

    account = 0
    derivedPrivateKey = bitcoin.bip32_ckd(bitcoin.bip32_ckd(bitcoin.bip32_ckd(priv, 44+HARDENED), HARDENED), HARDENED+account)
    print 'Derived private key:', derivedPrivateKey

    privateKey = bitcoin.encode_privkey(bitcoin.bip32_extract_key(derivedPrivateKey), 'wif_compressed')
    print 'private key (wif):\t', privateKey


    derivedPublicKey = bitcoin.bip32_privtopub(derivedPrivateKey)
    print 'Derived public key:', derivedPublicKey

    publicKeyHex = bitcoin.privtopub(privateKey)
    print 'public key (hex):\t', publicKeyHex

    address = bitcoin.pubtoaddr(publicKeyHex)
    print 'address:\t\t\t', address

    print ""
    print "Account public keys (XPUB)"
    xpubs = []
    for i in range(0, i):
        derivedPrivateKey = bitcoin.bip32_ckd(bitcoin.bip32_ckd(bitcoin.bip32_ckd(priv, 44+HARDENED), HARDENED), HARDENED+i)
        xpub = bitcoin.bip32_privtopub(derivedPrivateKey)
        print 'Account', i, 'xpub:', xpub
        xpubs.append(xpub)

    return xpubs




def bundleAddresses(addresses):
    bundle = ''
    for address in addresses:
        bundle += address + '|'

    bundle = bundle[:-1]
    return bundle


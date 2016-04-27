
import bitcoin
from mnemonic import *
from binascii import hexlify, unhexlify
import json

from pprint import pprint

HARDENED = 2**31

def getAddressesFromXPUB(xpub, i=10):
    addressList = []
    pub0 = bitcoin.bip32_ckd(xpub, 0)

    for i in range (0, i):
        publicKey = bitcoin.bip32_ckd(pub0, i)
        hexKey = bitcoin.encode_pubkey(bitcoin.bip32_extract_key(publicKey), 'hex_compressed')
        address_fromPub =  bitcoin.pubtoaddr(hexKey)
        addressList.append(address_fromPub)

    return addressList


def getPrivKey(xpriv, i):
    privkeys = {}
    priv0 = bitcoin.bip32_ckd(xpriv, 0)

    privateKey = bitcoin.bip32_ckd(priv0, i)
    wifKey = bitcoin.encode_privkey(bitcoin.bip32_extract_key(privateKey), 'wif_compressed')
    address_fromPriv =  bitcoin.privtoaddr(wifKey)
    privkeys[address_fromPriv] = wifKey

    return privkeys


def getPrivKeys(xpriv, i=10):
    privkeys = {}
    priv0 = bitcoin.bip32_ckd(xpriv, 0)

    for i in range (0, i):
        privateKey = bitcoin.bip32_ckd(priv0, i)
        wifKey = bitcoin.encode_privkey(bitcoin.bip32_extract_key(privateKey), 'wif_compressed')
        address_fromPriv =  bitcoin.privtoaddr(wifKey)
        privkeys[address_fromPriv] = wifKey

    return privkeys


def getChangeAddressesFromXPUB(xpub, i=10):
    addressList = []
    pub0 = bitcoin.bip32_ckd(xpub, 1)

    for i in range (0, i):
        publicKey = bitcoin.bip32_ckd(pub0, i)
        hexKey = bitcoin.encode_pubkey(bitcoin.bip32_extract_key(publicKey), 'hex_compressed')
        address_fromPub =  bitcoin.pubtoaddr(hexKey)
        addressList.append(address_fromPub)

    return addressList



def getTrezorXPUBKeys(mnemonic, passphrase="", i=1):

    myMnemonic = mnemonic
    passphrase = passphrase

    mnemo = Mnemonic('english')
    seed = hexlify(mnemo.to_seed(myMnemonic, passphrase=passphrase))

    priv = bitcoin.bip32_master_key(unhexlify(seed))

    account = 0
    derivedPrivateKey = bitcoin.bip32_ckd(bitcoin.bip32_ckd(bitcoin.bip32_ckd(priv, 44+HARDENED), HARDENED), HARDENED+account)

    xpubs = []
    for i in range(0, i):
        derivedPrivateKey = bitcoin.bip32_ckd(bitcoin.bip32_ckd(bitcoin.bip32_ckd(priv, 44+HARDENED), HARDENED), HARDENED+i)
        xpub = bitcoin.bip32_privtopub(derivedPrivateKey)
        xpubs.append(xpub)

    return xpubs


def getTrezorXPRIVKeys(mnemonic, passphrase="", i=1):

    myMnemonic = mnemonic
    passphrase = passphrase

    mnemo = Mnemonic('english')
    seed = hexlify(mnemo.to_seed(myMnemonic, passphrase=passphrase))

    priv = bitcoin.bip32_master_key(unhexlify(seed))

    account = 0
    derivedPrivateKey = bitcoin.bip32_ckd(bitcoin.bip32_ckd(bitcoin.bip32_ckd(priv, 44+HARDENED), HARDENED), HARDENED+account)

    xprivs = []
    for i in range(0, i):
        derivedPrivateKey = bitcoin.bip32_ckd(bitcoin.bip32_ckd(bitcoin.bip32_ckd(priv, 44+HARDENED), HARDENED), HARDENED+i)
        xprivs.append(derivedPrivateKey)

    return xprivs


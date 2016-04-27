# BitcoinSpellbook-v0.1
A collection of APIs and Webservices using the Bitcoin blockchain

author: Wouter Glorieux
website: www.valyrian.tech

APIs:
Blockchaindata      : Fetches data from multiple blockexplorers
SimplifiedInputsList: Simplify transactions into a list of address-value pairs
Blocklinker         : combines a SIL with an BIP44 extended public key
Bitvoter            : simple voting mechanism
ProportionalRandom  : chooses a random address from a SIL (chance of winning depends on value in SIL)

Webservices:
HDForwarder         : automatically forward bitcoins to next address in a BIP44 HD-wallet
DistributeBTC       : automatically distribute bitcoins based on a SIL or custom distribution
BitcoinWells        : reveal text or link or send email when a bitcoin address received an certain amount of bitcoins


Each of the modules are designed for the Google App Engine platform.
You will need to make a separate project for each of the modules.


Support further development:

1Woutere8RCF82AgbPCc5F4KuYVvS4meW
or
https://www.indiegogo.com/projects/bitcoin-spellbook


Special thanks to:
Vitalik Buterin for the pybitcointools library
https://github.com/vbuterin/pybitcointools

Marek Palatinus and Pavol Rusnak for the python-mnemonic library
https://github.com/trezor/python-mnemonic
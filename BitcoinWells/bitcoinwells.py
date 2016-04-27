#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import urllib2
import json
import hashlib
import hmac
import base64
import logging
import jinja2
import webapp2

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import mail
import datetime
import time
import re

import includes

from google.appengine.api import urlfetch
urlfetch.set_default_fetch_deadline(60)

MAIL_FROM = "Bitcoin Wells <wouter.glorieux@gmail.com>"
BLOCKCHAINDATA_URL = "https://blockchaindata.appspot.com"

SOCIALBUTTONS_ENABLED = False
REQUIRED_CONFIRMATIONS = 3 #must be at least 3


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
    mailFrom = ndb.StringProperty(indexed=False, default="your.name@example.com")
    APIkey = ndb.StringProperty(indexed=False, default="")
    APIsecret = ndb.StringProperty(indexed=False, default="") #must be a multiple of 4 characters!!!

def bitcoinWells_key():
    #Constructs a Master Datastore key
    return ndb.Key('BitcoinWells', 'BitcoinWells')

def well_key(well):
    #Constructs a Datastore key for a Well entity
    return ndb.Key('Well', str(well.key.id()))

def campaign_key(campaign):
    #Constructs a Datastore key for a Campaign entity
    return ndb.Key('Campaign', str(campaign.key.id()))

def milestone_key(milestone):
    #Constructs a Datastore key for a Milestone entity
    return ndb.Key('Milestone', str(milestone.key.id()))

class Well(ndb.Model):
    userID = ndb.StringProperty('u', default='', indexed=True)
    creator = ndb.StringProperty('c', default='')
    creatorEmail = ndb.StringProperty('e', default='')
    name = ndb.StringProperty('n', default='', indexed=True)
    address = ndb.StringProperty('a', default='', indexed=True)
    creationDate = ndb.DateTimeProperty('dt', auto_now_add=True)
    description = ndb.TextProperty('d', default='')
    youtube = ndb.StringProperty('y', default='')
    status = ndb.StringProperty('s', choices=['Pending', 'Active', 'Disabled'], default='Pending')
    visibility = ndb.StringProperty('v', choices=['Public', 'Private'], default='Private')
    tags = ndb.TextProperty('t', default='')
    sortOrder = ndb.IntegerProperty('o', default=0)



class Campaign(ndb.Model):
    wellID = ndb.StringProperty('i', default='', indexed=True)
    name = ndb.StringProperty('n', default='', indexed=True)
    creationDate = ndb.DateTimeProperty('dt', auto_now_add=True)
    description = ndb.TextProperty('d', default='')
    youtube = ndb.StringProperty('y', default='')
    target = ndb.IntegerProperty('t', default=0)
    startAmount = ndb.IntegerProperty('sa', default=0)

class Milestone(ndb.Model):
    wellID = ndb.StringProperty('wi', default='', indexed=True)
    campaignID = ndb.StringProperty('ci', default='', indexed=True)
    name = ndb.StringProperty('n', default='', indexed=True)
    date = ndb.DateTimeProperty('dt', auto_now_add=True)
    description = ndb.TextProperty('d', default='')
    percent = ndb.FloatProperty('t', default=0)
    action = ndb.StringProperty('a', choices=['None', 'RevealText', 'RevealLink', 'SendMail'], default='None')
    revealText = ndb.TextProperty('rt', default='')
    revealLinkText = ndb.StringProperty('rlt', default='')
    revealLinkURL = ndb.StringProperty('rlu', default='')
    mailTo = ndb.StringProperty('mt', default='someone@example.com')
    mailSubject = ndb.StringProperty('ms', default='Milestone achieved!')
    mailBody = ndb.TextProperty('mb', default='A milestone of your campaign has been achieved!')
    mailSent = ndb.BooleanProperty('sent', default=False)

def validEmail(email):
    valid = False
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        valid = True

    return valid

#this function will query blockchaindata.appspot.com and return a dictionary of confirmed balances
def getBalances(addresses):
    balances = {}
    parameters = Parameters.get_or_insert('DefaultConfig')

    url = parameters.blockchaindataURL + '/balances?addresses=' + toUrlString(addresses)
    try:
        ret = urllib2.urlopen(urllib2.Request(url))
        data = json.loads(ret.read())
    except:
        data = {}

    if 'success' in data and data['success'] == 1:
        balances = data['balances']

    return balances

#this function will concatenate all adresses and put '|' between them
def toUrlString(addresses):
    addrString = ''
    for address in addresses:
        addrString += address + '|'

    addrString = addrString[:-1]
    return addrString




class MainPage(webapp2.RequestHandler):

    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')
        wellID = 0
        TXS = []
        campaigns = []
        milestones = []
        totalReceived = 0
        totalTarget = 0
        donations = []
        if self.request.get('wellID'):
            wellID = int(self.request.get('wellID'))
            wells = [Well.get_by_id(wellID, parent=bitcoinWells_key())]

            url = parameters.blockchaindataURL + '/transactions?format=json&address=' + wells[0].address
            try:
                ret = urllib2.urlopen(urllib2.Request(url))
                data = json.loads(ret.read())
            except:
                data = {}

            if 'success' in data and data['success'] == 1:
                TXS = data['TXS']

                for i in range(0, len(TXS)):
                    if TXS[i]['receiving'] == True:
                        totalReceived += TXS[i]['receivedValue']
                        donations.append([TXS[i]['primeInputAddress'], TXS[i]['receivedValue']])



            campaigns_query = Campaign.query(Campaign.wellID == str(wellID), ancestor=well_key(wells[0])).order(Campaign.creationDate)
            if self.request.get('campaignID'):
                campaignID = int(self.request.get('campaignID'))
                campaigns = [Campaign.get_by_id(campaignID, parent=well_key(wells[0]))]
            else:
                campaigns = campaigns_query.fetch()



            for i in range(0, len(campaigns)):
                totalTarget += campaigns[i].target


        else:
            wells_query = Well.query(Well.visibility == 'Public', Well.status == 'Active', ancestor=bitcoinWells_key()).order(Well.sortOrder)
            wells = wells_query.fetch()

        wellAddresses = []
        for well in wells:
            wellAddresses.append(well.address)

        balances = getBalances(wellAddresses)

        maxChartValue = 0
        overflow = 0
        needed = 0
        if totalTarget >= totalReceived:
            maxChartValue = totalTarget
            needed = totalTarget - totalReceived
        else:
            maxChartValue = totalReceived
            overflow = totalReceived - totalTarget





        milestoneTicks = []
        for campaign in campaigns:
            milestones_query = Milestone.query(Milestone.wellID == str(wellID), Milestone.campaignID == str(campaign.key.id()), ancestor=campaign_key(campaign)).order(Milestone.percent)
            campaign.milestones = milestones_query.fetch()

            for milestone in reversed(campaign.milestones):
                if milestone.action != 'SendMail':
                    milestoneTicks.append((campaign.startAmount + int((campaign.target*milestone.percent)/100))/100000000.0)




        donationColors = []
        for donation in donations:
            donationColors.append('blue')
        donationColors.append('white')



        if len(campaigns) == 0:
            dummyCampaign = Campaign()
            dummyCampaign.name = "Total raised"
            dummyCampaign.target = totalReceived
            dummyCampaign.startAmount = 0
            campaigns = [dummyCampaign]

        elif overflow > 0:
            dummyCampaign = Campaign()
            dummyCampaign.name = "Overflow"
            dummyCampaign.target = overflow
            dummyCampaign.startAmount = totalReceived - overflow
            campaigns.append(dummyCampaign)

        isAdmin = False
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        if self.request.get('wellID') and self.request.get('format') == 'json':
            response = {'success': 1, 'well': {}}
            response['well']['ID'] = wellID
            response['well']['Name'] = well.name
            response['well']['Address'] = well.address
            response['well']['Description'] = well.description
            response['well']['Tags'] = well.tags
            response['well']['Creator'] = well.creator
            response['well']['CreatorEmail'] = well.creatorEmail
            response['well']['Youtube'] = well.youtube
            response['well']['Date'] = int(time.mktime(well.creationDate.timetuple()))
            response['well']['Status'] = well.status
            response['well']['Campaigns'] = []
            response['well']['Tags'] = well.tags
            response['well']['SortOrder'] = well.sortOrder
            response['well']['Balance'] = balances[well.address]

            for wellCampaign in campaigns:
                campaign = {}
                campaign['Name'] = wellCampaign.name
                campaign['Description'] = wellCampaign.description
                campaign['Youtube'] = wellCampaign.youtube
                campaign['TargetAmount'] = wellCampaign.target
                campaign['StartAmount'] = wellCampaign.startAmount

                if wellCampaign.name != 'Total raised':
                    campaign['ID'] = wellCampaign.key.id()
                    campaign['CreationDate'] = int(time.mktime(wellCampaign.creationDate.timetuple()))

                    milestones_query = Milestone.query(Milestone.wellID == str(wellID), Milestone.campaignID == str(campaign['ID']), ancestor=campaign_key(wellCampaign)).order(Milestone.percent)
                    milestones = milestones_query.fetch()

                    campaign['Milestones'] = []
                    for campaignMilestone in milestones:
                        milestone = {}
                        milestone['ID'] = campaignMilestone.key.id()
                        milestone['WellID'] = campaignMilestone.wellID
                        milestone['CampaignID'] = campaignMilestone.campaignID
                        milestone['Name'] = campaignMilestone.name
                        milestone['Description'] = campaignMilestone.description
                        milestone['Percent'] = campaignMilestone.percent
                        milestone['Action'] = campaignMilestone.action


                        if (balances[well.address]['received'] - wellCampaign.startAmount) >= (campaignMilestone.percent * wellCampaign.target)/100:

                            if campaignMilestone.action == 'RevealText':
                                milestone['RevealText'] = campaignMilestone.revealText
                            elif campaignMilestone.action == 'RevealLink':
                                milestone['RevealLinkText'] = campaignMilestone.revealLinkText
                                milestone['RevealLinkURL'] = campaignMilestone.revealLinkURL
                            '''
                            elif campaignMilestone.action == 'SendMail':
                                milestone['MailTo'] = campaignMilestone.mailTo
                                milestone['MailSubject'] = campaignMilestone.mailSubject
                                milestone['MailBody'] = campaignMilestone.mailBody
                                milestone['MailSent'] = campaignMilestone.mailSent
                            '''

                        campaign['Milestones'].append(milestone)

                    response['well']['Campaigns'].append(campaign)

                else:
                    campaign['ID'] = 0

            self.response.write(json.dumps(response))

        elif not self.request.get('wellID') and self.request.get('format') == 'json':
            response = {'success': 1, 'wells': []}
            for well in wells:
                tmpWell = {}
                tmpWell['ID'] = well.key.id()
                tmpWell['Name'] = well.name
                tmpWell['Address'] = well.address
                tmpWell['Description'] = well.description
                tmpWell['Tags'] = well.tags
                tmpWell['Creator'] = well.creator
                tmpWell['CreatorEmail'] = well.creatorEmail
                tmpWell['Youtube'] = well.youtube
                tmpWell['Date'] = int(time.mktime(well.creationDate.timetuple()))
                tmpWell['Status'] = well.status
                tmpWell['Tags'] = well.tags
                tmpWell['SortOrder'] = well.sortOrder
                tmpWell['Balance'] = balances[well.address]
                response['wells'].append(tmpWell)


            self.response.write(json.dumps(response))



        else:
            template_values = {
                'url': url,
                'url_linktext': url_linktext,

                'wells': wells,
                'balances': balances,
                'wellID': wellID,
                'timeNow': int(time.time()),
                'donations': donations,
                'nDonations': len(donations),
                'maxChartValue': maxChartValue,
                'campaigns': campaigns,
                'nCampaigns': len(campaigns),
                'milestones': milestones,
                'needed': needed,

                'donationColors': donationColors,
                'milestoneTicks': milestoneTicks,



                'cssHTML': includes.get_CssHTML(),
                'metaHTML': includes.get_MetaHTML(),
                'scriptsHTML': includes.get_ScriptsHTML(),
                'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
                'logoHTML': includes.get_LogoHTML(),
                'footerHTML': includes.get_FooterHTML(),
                'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),

                'socialButtons': SOCIALBUTTONS_ENABLED,


            }

            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))








class WellPage(webapp2.RequestHandler):

    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')
        isAdmin = False
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        wellID = 0
        well = Well(parent=bitcoinWells_key())
        campaigns = []
        if self.request.get('wellID'):
            wellID = int(self.request.get('wellID'))
            well = Well.get_by_id(wellID, parent=bitcoinWells_key())
            campaigns_query = Campaign.query(Campaign.wellID == str(wellID), ancestor=well_key(well)).order(-Campaign.creationDate)
            campaigns = campaigns_query.fetch()
        elif users.get_current_user():
            well.creator = users.get_current_user().nickname()
            well.creatorEmail = users.get_current_user().email()



        template_values = {
            'url': url,
            'url_linktext': url_linktext,
            'wellID': wellID,
            'well': well,
            'campaigns': campaigns,
            'cssHTML': includes.get_CssHTML(),
            'metaHTML': includes.get_MetaHTML(),
            'scriptsHTML': includes.get_ScriptsHTML(),
            'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
            'logoHTML': includes.get_LogoHTML(),
            'footerHTML': includes.get_FooterHTML(),
            'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
        }

        template = JINJA_ENVIRONMENT.get_template('well.html')
        self.response.write(template.render(template_values))


class SaveWell(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def post(self):
        if users.get_current_user():

            well = Well(parent=bitcoinWells_key())
            if self.request.get('WellID') not in ['', 0, 'None']:
                wellID = int(self.request.get('WellID'))
                well = Well.get_by_id(wellID, parent=bitcoinWells_key())

            well.name = self.request.get('WellName')
            well.address = self.request.get('WellAddress')
            well.description = self.request.get('Description')
            well.tags = self.request.get('WellTags')
            well.sortOrder = int(self.request.get('WellSortOrder'))
            well.creator = self.request.get('Creator')
            well.creatorEmail = self.request.get('CreatorEmail')

            well.youtube = self.request.get('Youtube')
            if self.request.get('Visibility') in ['Public', 'Private']:
                well.visibility = self.request.get('Visibility')

            if self.request.get('Status') in ['Pending', 'Active', 'Disabled']:
                well.status = self.request.get('Status')

            well_key = well.put()
            self.redirect('/well?wellID=' + str(well_key.id()))


class UpdateWell(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def post(self):
        error = ''
        wellID = 0
        response = {'success': 0}

        parameters = Parameters.get_or_insert('DefaultConfig')

        if 'API-Key' in self.request.headers:
            APIkey = self.request.headers['API-Key']
            if APIkey != parameters.APIkey and parameters.APIkey != '':
                error = 'Incorrect APIkey'
                response = {'success': 0, 'error': error}
        else:
            error = 'No APIkey supplied'
            response = {'success': 0, 'error': error}


        if 'API-Sign' in self.request.headers:
            signature = str(self.request.headers['API-Sign'])
            postdata = self.request.body
            message = hashlib.sha256(postdata).digest()
            if signature != base64.b64encode(hmac.new(base64.b64decode(parameters.APIsecret), message, hashlib.sha512).digest()):
                error =  'Invalid signature'
                response = {'success': 0, 'error': error}
        else:
            error = 'No signature supplied'
            response = {'success': 0, 'error': error}


        if self.request.get('ID') and error == '':
            try:
                wellID = int(self.request.get('ID'))
            except ValueError:
                error = 'ID must be an integer'
                response = {'success': 0, 'error': error}

            if error == '':
                well = Well(parent=bitcoinWells_key())
                if wellID != 0:
                    well = Well.get_by_id(wellID, parent=bitcoinWells_key())

                if self.request.get('Name'):
                    if len(self.request.get('Name')) > 0:
                        well.name = self.request.get('Name')
                    else:
                        error = 'Name cannot be empty'

                if self.request.get('Address'):
                    if len(self.request.get('Address')) > 0:
                        well.address = self.request.get('Address')
                    else:
                        error = 'Address cannot be empty'


                if self.request.get('Description'):
                    well.description = self.request.get('Description')

                if self.request.get('Creator'):
                    well.creator = self.request.get('Creator')

                if self.request.get('CreatorEmail'):
                    if validEmail(self.request.get('CreatorEmail')):
                        well.creatorEmail = self.request.get('CreatorEmail')
                    else:
                        error = 'Invalid email address'

                if self.request.get('Tags'):
                    well.tags = self.request.get('Tags')

                if self.request.get('Youtube'):
                    well.youtube = self.request.get('Youtube')

                if self.request.get('Visibility'):
                    if self.request.get('Visibility') in ['Public', 'Private']:
                        well.visibility = self.request.get('Visibility')
                    else:
                        error = 'Visibility must be Public or Private'

                if self.request.get('Status'):
                    if self.request.get('Status') in ['Pending', 'Active', 'Disabled']:
                        well.status = self.request.get('Status')
                    else:
                        error = 'Status must be Pending, Active or Disabled'

                if self.request.get('SortOrder'):
                    sortOrder = -1
                    try:
                        sortOrder = int(self.request.get('SortOrder'))
                    except ValueError:
                        error = 'SortOrder must be a positive integer or equal to 0'

                    if sortOrder >= 0:
                        well.sortOrder = sortOrder
                    else:
                        error = 'SortOrder must be a positive integer or equal to 0'

                if error == '':
                    well.put()

                    response['success'] = 1
                    tmpWell = {}
                    tmpWell['ID'] = well.key.id()
                    tmpWell['Name'] = well.name
                    tmpWell['Address'] = well.address
                    tmpWell['Description'] = well.description
                    tmpWell['Creator'] = well.creator
                    tmpWell['CreatorEmail'] = well.creatorEmail
                    tmpWell['Youtube'] = well.youtube
                    tmpWell['Status'] = well.status
                    tmpWell['Visibility'] = well.visibility
                    tmpWell['Date'] = int(time.mktime(well.creationDate.timetuple()))
                    tmpWell['Tags'] = well.tags
                    tmpWell['SortOrder'] = well.sortOrder
                    response['well'] = tmpWell

                    self.response.write(json.dumps(response))
                else:
                    response['success'] = 0
                    response['error'] = error
                    self.response.write(json.dumps(response))

            else:
                self.response.write(json.dumps(response))

        else:
            self.response.write(json.dumps(response))




class CampaignPage(webapp2.RequestHandler):

    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')
        isAdmin = False
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        wellID = 0
        if self.request.get('wellID'):
            wellID = int(self.request.get('wellID'))
            well = Well.get_by_id(wellID, parent=bitcoinWells_key())

        campaign = ''
        campaignID = 0
        milestones = []
        if self.request.get('campaignID'):
            campaignID = int(self.request.get('campaignID'))
            campaign = Campaign.get_by_id(campaignID, parent=well_key(well))

            milestones_query = Milestone.query(Milestone.wellID == str(wellID), Milestone.campaignID == str(campaignID), ancestor=campaign_key(campaign)).order(Milestone.percent)
            milestones = milestones_query.fetch()


        template_values = {
            'wellID': wellID,
            'well': well,
            'campaignID': campaignID,
            'campaign': campaign,
            'milestones': milestones,
            'url': url,
            'url_linktext': url_linktext,
            'cssHTML': includes.get_CssHTML(),
            'metaHTML': includes.get_MetaHTML(),
            'scriptsHTML': includes.get_ScriptsHTML(),
            'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
            'logoHTML': includes.get_LogoHTML(),
            'footerHTML': includes.get_FooterHTML(),
            'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
        }

        template = JINJA_ENVIRONMENT.get_template('campaign.html')
        self.response.write(template.render(template_values))


class SaveCampaign(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def post(self):
        if users.get_current_user() and self.request.get('WellID') != "":
            wellID = int(self.request.get('WellID'))
            well = Well.get_by_id(wellID, parent=bitcoinWells_key())
            campaign = Campaign(parent=well_key(well))
            campaign.wellID = str(wellID)



            if self.request.get('CampaignID'):
                campaignID = int(self.request.get('CampaignID'))
                if campaignID != 0:
                    campaign = Campaign.get_by_id(campaignID, parent=well_key(well))

            campaign.name = self.request.get('CampaignName')
            campaign.description = self.request.get('CampaignDescription')
            campaign.youtube = self.request.get('CampaignYoutube')

            if campaign.target != int(self.request.get('CampaignTarget')):
                campaign.target = int(self.request.get('CampaignTarget'))
                campaign_key = campaign.put()
                self.redirect('/updateStartAmounts?wellID=' + self.request.get('WellID'))
            else:
                campaign_key = campaign.put()
                self.redirect('/campaign?wellID=' + campaign.wellID + '&campaignID=' + str(campaign_key.id()))

        else:
            self.redirect('/admin?')


class UpdateCampaign(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def post(self):
        error = ''
        wellID = 0
        campaignID = 0
        response = {'success': 0}

        parameters = Parameters.get_or_insert('DefaultConfig')

        if 'API-Key' in self.request.headers:
            APIkey = self.request.headers['API-Key']
            if APIkey != parameters.APIkey and parameters.APIkey != '':
                error = 'Incorrect APIkey'
                response = {'success': 0, 'error': error}
        else:
            error = 'No APIkey supplied'
            response = {'success': 0, 'error': error}


        if 'API-Sign' in self.request.headers:
            signature = str(self.request.headers['API-Sign'])
            postdata = self.request.body
            message = hashlib.sha256(postdata).digest()
            if signature != base64.b64encode(hmac.new(base64.b64decode(parameters.APIsecret), message, hashlib.sha512).digest()):
                error =  'Invalid signature'
                response = {'success': 0, 'error': error}
        else:
            error = 'No signature supplied'
            response = {'success': 0, 'error': error}


        if self.request.get('ID') and self.request.get('WellID')and error == '':
            try:
                campaignID = int(self.request.get('ID'))
            except ValueError:
                error = 'ID must be an integer'
                response = {'success': 0, 'error': error}

            try:
                wellID = int(self.request.get('WellID'))
                well = Well.get_by_id(wellID, parent=bitcoinWells_key())
            except ValueError:
                error = 'WellID must be an integer'
                response = {'success': 0, 'error': error}


            if error == '':
                campaign = Campaign(parent=well_key(well))
                campaign.wellID = str(wellID)
                if campaignID != 0:
                    campaign = Campaign.get_by_id(campaignID, parent=well_key(well))

                if self.request.get('Name'):
                    if len(self.request.get('Name')) > 0:
                        campaign.name = self.request.get('Name')
                    else:
                        error = 'Name cannot be empty'

                if self.request.get('Description'):
                    campaign.description = self.request.get('Description')


                if self.request.get('Youtube'):
                    campaign.youtube = self.request.get('Youtube')


                if self.request.get('TargetAmount'):
                    amount = -1
                    try:
                        amount = int(self.request.get('TargetAmount'))
                    except ValueError:
                        error = 'TargetAmount must be a positive integer or equal to 0 (in Satoshis)'

                    if amount >= 0:
                        campaign.target = amount
                    else:
                        error = 'TargetAmount must be a positive integer or equal to 0 (in Satoshis)'


                if error == '':
                    campaign.put()

                    response['success'] = 1
                    tmpCampaign = {}
                    tmpCampaign['ID'] = campaign.key.id()
                    tmpCampaign['WellID'] = campaign.wellID
                    tmpCampaign['Name'] = campaign.name
                    tmpCampaign['Description'] = campaign.description
                    tmpCampaign['Youtube'] = campaign.youtube
                    tmpCampaign['TargetAmount'] = campaign.target
                    tmpCampaign['StartAmount'] = campaign.startAmount
                    tmpCampaign['Date'] = int(time.mktime(campaign.creationDate.timetuple()))
                    response['campaign'] = tmpCampaign


                    #update all startamounts
                    campaigns_query = Campaign.query(Campaign.wellID == campaign.wellID, ancestor=well_key(well)).order(Campaign.creationDate)
                    campaigns = campaigns_query.fetch()

                    previousTarget = 0
                    for otherCampaign in campaigns:
                        otherCampaign.startAmount = previousTarget
                        previousTarget = otherCampaign.startAmount + otherCampaign.target
                        otherCampaign.put()

                    self.response.write(json.dumps(response))
                else:
                    response['success'] = 0
                    response['error'] = error
                    self.response.write(json.dumps(response))

            else:
                self.response.write(json.dumps(response))

        else:
            self.response.write(json.dumps(response))





class UpdateStartAmounts(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def get(self):
        if users.get_current_user() and self.request.get('wellID'):
            wellID = int(self.request.get('wellID'))
            well = Well.get_by_id(wellID, parent=bitcoinWells_key())
            campaigns = []
            campaigns_query = Campaign.query(Campaign.wellID == str(self.request.get('wellID')), ancestor=well_key(well)).order(Campaign.creationDate)
            campaigns = campaigns_query.fetch()

            previousTarget = 0
            for campaign in campaigns:
                campaign.startAmount = previousTarget
                previousTarget = campaign.startAmount + campaign.target
                campaign.put()

            self.redirect('/well?wellID=' + self.request.get('wellID') )

class MilestonePage(webapp2.RequestHandler):

    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')
        isAdmin = False
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        wellID = 0
        campaignID = 0
        milestoneID = 0
        milestone = []
        if self.request.get('wellID'):
            wellID = int(self.request.get('wellID'))
            well = Well.get_by_id(wellID, parent=bitcoinWells_key())

            if self.request.get('campaignID'):
                campaignID = int(self.request.get('campaignID'))
                campaign = Campaign.get_by_id(campaignID, parent=well_key(well))

                if self.request.get('milestoneID'):
                    milestoneID = int(self.request.get('milestoneID'))
                    milestone = Milestone.get_by_id(milestoneID, parent=campaign_key(campaign))


        template_values = {
            'wellID': wellID,
            'well': well,
            'campaignID': campaignID,
            'campaign': campaign,
            'milestoneID': milestoneID,
            'milestone': milestone,
            'url': url,
            'url_linktext': url_linktext,
            'cssHTML': includes.get_CssHTML(),
            'metaHTML': includes.get_MetaHTML(),
            'scriptsHTML': includes.get_ScriptsHTML(),
            'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
            'logoHTML': includes.get_LogoHTML(),
            'footerHTML': includes.get_FooterHTML(),
            'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
        }

        template = JINJA_ENVIRONMENT.get_template('milestone.html')
        self.response.write(template.render(template_values))


class SaveMilestone(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def post(self):
        if users.get_current_user() and self.request.get('WellID') != 0:
            wellID = int(self.request.get('WellID'))
            well = Well.get_by_id(wellID, parent=bitcoinWells_key())

            if self.request.get('CampaignID'):
                campaignID = int(self.request.get('CampaignID'))
                campaign = Campaign.get_by_id(campaignID, parent=well_key(well))

                milestone = Milestone(parent=campaign_key(campaign))
                if self.request.get('MilestoneID'):
                    milestoneID = int(self.request.get('MilestoneID'))
                    if milestoneID != 0:
                        milestone = Milestone.get_by_id(milestoneID, parent=campaign_key(campaign))


                milestone.campaignID = self.request.get('CampaignID')
                milestone.wellID = self.request.get('WellID')

                milestone.name = self.request.get('MilestoneName')
                milestone.description = self.request.get('MilestoneDescription')
                milestone.percent = float(self.request.get('MilestonePercent'))
                milestone.action = self.request.get('MilestoneAction')
                milestone.revealText = self.request.get('RevealText')

                milestone.revealLinkText = self.request.get('RevealLinkText')
                milestone.revealLinkURL = self.request.get('RevealLinkURL')

                milestone.mailTo = self.request.get('MailTo')
                milestone.mailSubject = self.request.get('MailSubject')
                milestone.mailBody = self.request.get('MailBody')

                milestone_key = milestone.put()
                self.redirect('/milestone?wellID=' + str(milestone.wellID) + '&campaignID=' + str(milestone.campaignID) + '&milestoneID=' + str(milestone_key.id()))

class UpdateMilestone(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def post(self):
        error = ''
        wellID = 0
        campaignID = 0
        milestoneID = 0
        response = {'success': 0}

        parameters = Parameters.get_or_insert('DefaultConfig')

        if 'API-Key' in self.request.headers:
            APIkey = self.request.headers['API-Key']
            if APIkey != parameters.APIkey and parameters.APIkey != '':
                error = 'Incorrect APIkey'
                response = {'success': 0, 'error': error}
        else:
            error = 'No APIkey supplied'
            response = {'success': 0, 'error': error}


        if 'API-Sign' in self.request.headers:
            signature = str(self.request.headers['API-Sign'])
            postdata = self.request.body
            message = hashlib.sha256(postdata).digest()
            if signature != base64.b64encode(hmac.new(base64.b64decode(parameters.APIsecret), message, hashlib.sha512).digest()):
                error =  'Invalid signature'
                response = {'success': 0, 'error': error}
        else:
            error = 'No signature supplied'
            response = {'success': 0, 'error': error}


        if self.request.get('ID') and self.request.get('WellID') and self.request.get('CampaignID') and error == '':
            try:
                milestoneID = int(self.request.get('ID'))
            except ValueError:
                error = 'ID must be an integer'
                response = {'success': 0, 'error': error}

            try:
                wellID = int(self.request.get('WellID'))
                well = Well.get_by_id(wellID, parent=bitcoinWells_key())
            except ValueError:
                error = 'WellID must be an integer'
                response = {'success': 0, 'error': error}

            try:
                campaignID = int(self.request.get('CampaignID'))
                campaign = Campaign.get_by_id(campaignID, parent=well_key(well))
            except ValueError:
                error = 'CampaignID must be an integer'
                response = {'success': 0, 'error': error}

            if error == '':
                milestone = Milestone(parent=campaign_key(campaign))
                milestone.wellID = str(wellID)
                milestone.campaignID = str(campaignID)
                if milestoneID != 0:
                    milestone = Milestone.get_by_id(milestoneID, parent=campaign_key(campaign))

                if self.request.get('Name'):
                    if len(self.request.get('Name')) > 0:
                        milestone.name = self.request.get('Name')
                    else:
                        error = 'Name cannot be empty'

                if self.request.get('Description'):
                    milestone.description = self.request.get('Description')


                if self.request.get('Percent'):
                    percent = -1
                    try:
                        percent = float(self.request.get('Percent'))
                    except ValueError:
                        error = 'Percent must be a positive number between 0 and 100'

                    if percent >= 0:
                        milestone.percent = percent
                    else:
                        error = 'Percent must be a positive number between 0 and 100'

                if self.request.get('Action'):
                    if self.request.get('Action') in ['None', 'RevealText', 'RevealLink', 'SendMail']:
                        milestone.action = self.request.get('Action')
                    else:
                        error = 'Action must be None, RevealText, RevealLink or SendMail'

                if self.request.get('RevealText'):
                    milestone.revealText = self.request.get('RevealText')

                if self.request.get('RevealLinkText'):
                    milestone.revealLinkText = self.request.get('RevealLinkText')

                if self.request.get('RevealLinkURL'):
                    milestone.revealLinkURL = self.request.get('RevealLinkURL')


                if self.request.get('MailTo'):
                    if validEmail(self.request.get('MailTo')):
                        milestone.mailTo = self.request.get('MailTo')
                    else:
                        error = 'Invalid email address'

                if self.request.get('MailSubject'):
                    milestone.mailSubject = self.request.get('MailSubject')

                if self.request.get('MailBody'):
                    milestone.mailBody = self.request.get('MailBody')

                if self.request.get('MailSent') == 'False':
                    milestone.mailSent = False


                if error == '':
                    milestone.put()

                    response['success'] = 1
                    tmpMilestone = {}
                    tmpMilestone['ID'] = milestone.key.id()
                    tmpMilestone['WellID'] = milestone.wellID
                    tmpMilestone['CampaignID'] = milestone.campaignID
                    tmpMilestone['Name'] = milestone.name
                    tmpMilestone['Description'] = milestone.description
                    tmpMilestone['Percent'] = milestone.percent
                    tmpMilestone['Action'] = milestone.action

                    if milestone.action == 'RevealText':
                        tmpMilestone['RevealText'] = milestone.revealText
                    elif milestone.action == 'RevealLink':
                        tmpMilestone['RevealLinkText'] = milestone.revealLinkText
                        tmpMilestone['RevealLinkURL'] = milestone.revealLinkURL
                    elif milestone.action == 'SendMail':
                        tmpMilestone['MailTo'] = milestone.mailTo
                        tmpMilestone['MailSubject'] = milestone.mailSubject
                        tmpMilestone['MailBody'] = milestone.mailBody
                        tmpMilestone['MailSent'] = milestone.mailSent


                    response['milestone'] = tmpMilestone

                    self.response.write(json.dumps(response))
                else:
                    response['success'] = 0
                    response['error'] = error
                    self.response.write(json.dumps(response))

            else:
                self.response.write(json.dumps(response))

        else:
            self.response.write(json.dumps(response))





class CheckSendMail(webapp2.RequestHandler):

    def get(self):

        wells_query = Well.query(Well.status == 'Active', ancestor=bitcoinWells_key()).order(Well.sortOrder)
        wells = wells_query.fetch()

        for well in wells:
            balances = getBalances([well.address])
            if balances != {}:
                campaigns_query = Campaign.query(Campaign.wellID == str(well.key.id()), ancestor=well_key(well)).order(Campaign.creationDate)
                campaigns = campaigns_query.fetch()

                for campaign in campaigns:
                    milestones_query = Milestone.query(Milestone.wellID == str(well.key.id()), Milestone.campaignID == str(campaign.key.id()), Milestone.action == 'SendMail', Milestone.mailSent == False, ancestor=campaign_key(campaign)).order(Milestone.percent)
                    milestones = milestones_query.fetch()

                    for milestone in milestones:
                        if balances[well.address]['received'] >= (milestone.percent * campaign.target)/100 + campaign.startAmount:
                            logging.info('Milestone reached! Sending mail to ' + milestone.mailTo)
                            if validEmail(milestone.mailTo):
                                try:
                                    parameters = Parameters.get_or_insert('DefaultConfig')
                                    mail.send_mail(parameters.mailFrom, milestone.mailTo, milestone.mailSubject, milestone.mailBody)
                                    milestone.mailSent = True
                                    milestone.put()
                                    logging.info('Mail sent successfully.')
                                except:
                                    logging.error("Failed to send mail")
                            else:
                                logging.error("Invalid email address: " + milestone.mailTo)

            else:
                logging.error("Unable to retrieve balances for address " + well.address)


class AdminPage(webapp2.RequestHandler):

    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')
        status = ''
        if self.request.get('status') and self.request.get('status') != 'All':
            status = self.request.get('status')
            wells_query = Well.query(Well.status == status, ancestor=bitcoinWells_key()).order(Well.sortOrder)
        else:
            wells_query = Well.query(ancestor=bitcoinWells_key()).order(Well.sortOrder)

        wells = wells_query.fetch()

        isAdmin = False
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

            
        template_values = {
            'wells': wells,
            'status': status,

            'cssHTML': includes.get_CssHTML(),
            'metaHTML': includes.get_MetaHTML(),
            'scriptsHTML': includes.get_ScriptsHTML(),
            'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
            'logoHTML': includes.get_LogoHTML(),
            'footerHTML': includes.get_FooterHTML(),
            'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
        }

        template = JINJA_ENVIRONMENT.get_template('admin.html')
        self.response.write(template.render(template_values))


class DeleteWell(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def get(self):
        if users.get_current_user() and self.request.get('wellID'):
            wellID = int(self.request.get('wellID'))
            if wellID != 0:
                well = Well.get_by_id(wellID, parent=bitcoinWells_key())
                if well:
                    well.key.delete()

        self.redirect('/admin?')


class DeleteCampaign(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def get(self):
        if users.get_current_user() and self.request.get('wellID') and self.request.get('campaignID'):
            wellID = int(self.request.get('wellID'))
            well = Well.get_by_id(wellID, parent=bitcoinWells_key())
            campaignID = int(self.request.get('campaignID'))
            if campaignID != 0:
                campaign = Campaign.get_by_id(campaignID, parent=well_key(well))
                if campaign:
                    wellID = campaign.wellID
                    campaign.key.delete()
                    self.redirect('/well?wellID=' + str(wellID))
                else:
                    self.redirect('/admin?')
        else:
            self.redirect('/admin?')



class DeleteMilestone(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def get(self):
        if users.get_current_user() and self.request.get('wellID') and self.request.get('campaignID') and self.request.get('milestoneID'):
            wellID = int(self.request.get('wellID'))
            well = Well.get_by_id(wellID, parent=bitcoinWells_key())

            if self.request.get('campaignID'):
                campaignID = int(self.request.get('campaignID'))
                campaign = Campaign.get_by_id(campaignID, parent=well_key(well))

                milestoneID = int(self.request.get('milestoneID'))
                if milestoneID != 0:
                    milestone = Milestone.get_by_id(milestoneID, parent=campaign_key(campaign))
                    wellID = milestone.wellID
                    campaignID = milestone.campaignID
                    milestone.key.delete()

                self.redirect('/campaign?wellID=' + str(wellID) + '&campaignID=' + str(campaignID))
        else:
            self.redirect('/admin')

class ConfirmPage(webapp2.RequestHandler):
    @ndb.transactional(xg=True)
    def get(self):
        parameters = Parameters.get_or_insert('DefaultConfig')
        isAdmin = False
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        wellID = 0
        campaignID = 0
        milestoneID = 0

        well = []
        campaign = []
        milestone = []

        if users.get_current_user() and self.request.get('wellID'):
            wellID = int(self.request.get('wellID'))
            if wellID != 0:
                well = Well.get_by_id(wellID, parent=bitcoinWells_key())

                if self.request.get('campaignID'):
                    campaignID = int(self.request.get('campaignID'))
                    campaign = Campaign.get_by_id(campaignID, parent=well_key(well))

                    if self.request.get('milestoneID'):
                        milestoneID = int(self.request.get('milestoneID'))
                        if milestoneID != 0:
                            milestone = Milestone.get_by_id(milestoneID, parent=campaign_key(campaign))

                template_values = {
                    'well': well,
                    'campaign': campaign,
                    'milestone': milestone,

                    'wellID': wellID,
                    'campaignID': campaignID,
                    'milestoneID': milestoneID,

                    'cssHTML': includes.get_CssHTML(),
                    'metaHTML': includes.get_MetaHTML(),
                    'scriptsHTML': includes.get_ScriptsHTML(),
                    'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
                    'logoHTML': includes.get_LogoHTML(),
                    'footerHTML': includes.get_FooterHTML(),
                    'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
                }

                template = JINJA_ENVIRONMENT.get_template('confirm.html')
                self.response.write(template.render(template_values))
        else:
            self.redirect('/admin?')

class Documentation(webapp2.RequestHandler):
    def get(self):

        isAdmin = False
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            isAdmin = users.is_current_user_admin()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        parameters = Parameters.get_or_insert('DefaultConfig')

        template_values = {
            'Title': 'Bitcoin Wells documentation',
            'cssHTML': includes.get_CssHTML(),
            'metaHTML': includes.get_MetaHTML(),
            'scriptsHTML': includes.get_ScriptsHTML(),
            'navigationHTML': includes.get_NavigationHTML(url, url_linktext, Spellbook(parameters), isAdmin),
            'logoHTML': includes.get_LogoHTML(),
            'footerHTML': includes.get_FooterHTML(),
            'googleAnalyticsHTML': includes.get_GoogleAnalyticsHTML(parameters.trackingID),
        }

        template = JINJA_ENVIRONMENT.get_template('documentation.html')

        self.response.write(template.render(template_values))






application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/documentation', Documentation),
    ('/well', WellPage),
    ('/deleteWell', DeleteWell),
    ('/saveWell', SaveWell),
    ('/updateWell', UpdateWell),
    ('/updateCampaign', UpdateCampaign),
    ('/updateMilestone', UpdateMilestone),
    ('/campaign', CampaignPage),
    ('/saveCampaign', SaveCampaign),
    ('/deleteCampaign', DeleteCampaign),
    ('/updateStartAmounts', UpdateStartAmounts),
    ('/checkSendMail', CheckSendMail),
    ('/milestone', MilestonePage),
    ('/saveMilestone', SaveMilestone),
    ('/deleteMilestone', DeleteMilestone),
    ('/admin', AdminPage),
    ('/confirm', ConfirmPage),


], debug=True)

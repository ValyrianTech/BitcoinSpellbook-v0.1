#HTML includes



def get_FooterHTML():
     html = "<div id='copyright' class='container'>"
     html += "<p>More info: <a href='http://www.valyrian.tech'>www.valyrian.tech</a> | Twitter: <a href='http://www.twitter.com/wouterglorieux'>@wouterglorieux</a> </p>"
     html += "<p>Tip jar: <a href='https://www.blocktrail.com/BTC/address/1Woutere8RCF82AgbPCc5F4KuYVvS4meW'>1Woutere8RCF82AgbPCc5F4KuYVvS4meW</a></p>"
     html += "</div>"

     return html

def get_NavigationHTML(spellbook_urls=[]):
    html = "<div id='header-wrapper'>"
    html += "<div id='header' class='container'>"

    html += "<div class='menu-wrap'>"
    html += "<nav class='menu'>"

    html += "<ul class='clearfix'>"
    html += "<li><a href='/' accesskey='1' title=''>Bitcoin Spellbook <span class='arrow'>&#9660;</span></a>"
    html += "<ul class='sub-menu'>"

    for i in range(0, len(spellbook_urls)):
        html += "<li><a href=" + spellbook_urls[i]['url'] + ">"+ spellbook_urls[i]['name'] + "</a></li>"


    html += "</ul></li>"

    html += "<li><a href='/documentation' accesskey='2' title=''>API Documentation</a></li>"
    html += "</ul></div></div></div>"
    html += "</nav></div>"
    return html


def get_LogoHTML():
    html = ""
    return html


def get_CssHTML():
    html = "<link href='http://fonts.googleapis.com/css?family=Source+Sans+Pro:200,300,400,600,700,900' rel='stylesheet' />"
    html += "<link href='stylesheets/Spellbook.css' rel='stylesheet' type='text/css' media='all' />"
    html += "<link href='stylesheets/Blockchaindata.css' rel='stylesheet' type='text/css'>"
    return html

def get_MetaHTML():
    html = "<meta http-equiv='Content-Type' content='text/html; charset=iso-8859-1'>"
    html += "<META name='DistributeBTC'><META name='keywords' content='Bitcoin, Blockchain, Bitcoin Spellbook, Blockchaindata, Simplified Inputs List, Blocklinker, Proportional Random, Bitvoter, HDForwarder, DistributeBTC, BitcoinWells, Valyrian Tech'>"
    return html

def get_ScriptsHTML():
    html = "<script type='text/javascript' language='Javascript' src='http://code.jquery.com/jquery-1.10.1.min.js'></script>"
    html += "<script type='text/javascript' language='Javascript' src='http://code.jquery.com/jquery-migrate-1.2.1.min.js'></script>"       

    return html


def get_GoogleAnalyticsHTML(trackingID=""):
    html = ""
    if trackingID != "":
        html = "<div ID='GoogleAnalytics'>"
        html += "<script>"
        html += " (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){"
        html += " (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),"
        html += " m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)"
        html += " })(window,document,'script','//www.google-analytics.com/analytics.js','ga');"

        html += " ga('create', '" + str(trackingID) + "', 'auto');"
        html += " ga('send', 'pageview');"

        html += "</script></div>"

    return html



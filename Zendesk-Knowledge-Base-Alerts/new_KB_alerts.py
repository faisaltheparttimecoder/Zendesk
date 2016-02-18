# -*- coding: utf-8 -*-

#############################################################################################
#                                 Python program                                            #
#                       Written with python code version 2.7                                #
#                                                                                           #
# The program is to find the list of articles created or updated in the last one week       #
# using ZenDesk API and then send email to the group.                                       #
#                                                                                           #
# Naming convention used:                                                                   #
#   fn_ = function   ,  v_ = variable                                                       #
#    l_ = list       ,  d_ = dictionary                                                     #
#                                                                                           #
#############################################################################################


# Importing modules needed for the program
# If the import modules fail then install using "pip install <module-name>"


import requests
import json
import dateutil.parser
import datetime
import logging
from datetime import timedelta
from operator import itemgetter
import jinja2
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys, getopt


# Global parameters

# Set up a logging process
# Format of logging message on the screen " time [logging level] message "


formats = '%(asctime)s [%(levelname)s] %(message)s'
logger = logging.getLogger(__file__)


# Function: fn_logger_args
# Checking if the debug options are supplied with the call of the program
# if yes then turn on the DEBUG logging level
# else print the basic INFO messages


def fn_logger_args(argv):
    try:
        opts, args = getopt.getopt(argv, "hh:d", ["help", "debug"])
    except getopt.GetoptError:
        print ("Invalid Option, Use the below command to run debug")
        print ("{0} -d [--debug] ".format(__file__))
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print ("{} -d [--debug] ".format(__file__))
            sys.exit(2)
        elif opt in ("-d", "--debug"):
            logging.basicConfig(format=formats, level=logging.DEBUG)
    logging.basicConfig(format=formats, level=logging.INFO)

if __name__ == "__main__":
   fn_logger_args(sys.argv[1:])


# Parameters for authenticating the access to pull the API


username = "username@email.com"
password = "mypassword"


# Authenticate the username / password here and set it globally
# This authentications is used by the functions fn_get_categories_id() & fn_get_articles_info()


zd = requests.session()
zd.auth = (username, password)


# Parameters : v_CheckDays ( default to a week )
# This parameter is used by main()
# This is used to check the days we are interested in obtaining the article information.


v_CheckDays = 8


# Global Functions

# Function : fn_json_formatter
# This function is not important as it has been commented out at most places
# This is used to format the json output to better understand the json output ( for debugging )


def fn_json_formatter(jsondata):
    jsonformatter = json.dumps(jsondata, indent=4, sort_keys=True)
    print (jsonformatter)


# Function : fn_get_page_count
# Picks up the total pages under a url, this can be used to increment the web crawling


def fn_get_page_count(url):
    headers = {'Content-Type': 'application/json'}
    response = zd.get(url, headers=headers)
    data = response.json()
    return data['page_count']


# Function : fn_write_to_file(data)
# The below function get the data from main() and write to a file with HTML tag
# The HTML tag is created by jinja2 framework


def fn_write_to_file(data):
    filename = 'new-article-list.html'
    logger.debug("Saving the html comtent to file: '{}'".format(filename))
    fob = open(filename, 'w')
    # Used "encode" hack to avoid the error from the trademark symbol used by the categories section
    #              "UnicodeEncodeError: 'ascii' codec can't encode character u'\xae' in position"
    fob.write(data.encode('ascii', 'ignore'))
    fob.close()


# Function : fn_send_email(html)
# The below function get the data from main() and send email to the receipt's


def fn_send_email(html):

    # Sender and receiver email address

    me = "new-articles-alert@noreply.company.com"
    # If you want to add multiple receipents then add them like this
    # you = ["abc@xyz.com", "xyz@abc.com"]
    you = ["abc@efg.com"]

    # Create message container - the correct MIME type is multipart/alternative.

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "New articles published / updated past " + str(v_CheckDays) + " day"
    msg['From'] = me
    msg['To'] = ", ".join(you)

    # Create the body of the message (HTML version).

    part2 = MIMEText(html.encode('ascii', 'ignore'), 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.

    msg.attach(part2)

    # Send the message via local SMTP server.
    # Check Youtube on how to install postfix to configure SMTP on your server

    smtplib.SMTP()
    server = smtplib.SMTP('localhost.localdomain')
    logger.debug("SMTP server: '{}'".format(server))

    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.

    logger.info("Sending email to: '{0}' from: '{1}'".format(you,me))
    server.sendmail(me, you, msg.as_string())
    server.quit()


# Step 1:
# Get all the zendesk API , its manual and this is obtained from
# https://developer.zendesk.com/rest_api/docs/help_center/articles

# Enter you org URL
v_top_level_url = "https://discuss.zendesk.com"

d_zdapi = {
"articles" : v_top_level_url + "/api/v2/help_center/articles.json",
"categories" : v_top_level_url + "/api/v2/help_center/en-us/categories.json",
"sub_catergories" : v_top_level_url + "/api/v2/help_center/categories/{id}/articles.json",
"sections" : v_top_level_url + "/api/v2/help_center/sections.json",
"sub_sections": v_top_level_url + "api/v2/help_center/sections/{id}/articles.json"
}


# Step 2:
# Get the categories ID of the products that we are interested
# Below is the categories list that we will be pulling the information of. 
#
# Used "decode" Hack to avoid the error due to trademark symbol on its name.
#           "UnicodeWarning: Unicode equal comparison failed to convert both arguments to Unicode"


# Enter categories interested to send alerts
l_CategoryNames = [
    "Pivotal Greenplum DB Knowledge Base",
    "Pivotal Greenplum DB Knowledge Base (Internal)",
    "Pivotal DCA Knowledge Base",
    "Pivotal HD Knowledge Base",
    "Pivotal GemFire Knowledge Base",
    "Pivotal GemFire XD / SQLFire Knowledge Base",
    "Pivotal VRP Knowledge Base",
    "Spring IO Knowledge Base",
    "Pivotal GPText Knowledge Base",
    "Pivotal Cloud Foundry® Knowledge Base".decode('utf-8')
]


# Step 3:
# Function : get_categories_id
# This function loops into the Zendesk API to find the categories ID for product that is of interest
# We then store all those categories dictionary on a single list


def fn_get_categories_id():

    # Local variables

    l_categories = []
    v_currentpage = 1
    logger.debug("Categories current page: '{}'".format(v_currentpage))
    headers = {'Content-Type': 'application/json'}

    # Get the API for categories from the d_zdapi mentioned above

    v_pageurl = d_zdapi['categories']
    logger.debug("Categories URL: '{}'".format(v_pageurl))

    # Get the max number of pages on the URL, so that we can crawl till the end of the page.

    v_maxpage = fn_get_page_count(v_pageurl)
    logger.info("Categories max pages: '{}'".format(v_maxpage))

    # Loop till we reach the end of the page.

    while v_currentpage <= v_maxpage:

        # The URL changes on every page , the below parameter makes those adjustment

        v_pageurlincrement = v_pageurl + "?page=" + str(v_currentpage)
        logger.info("Reading Categories URL: '{}'".format(v_pageurlincrement))

        # Get the data from the url page

        response = zd.get(v_pageurlincrement, headers=headers)
        data = response.json()
        # print (fn_json_formatter((data)))

        # Loop through the data obtained from the API
        # and just pick the information we are interested set by l_CategoryNames and append it to the list
        # we delete descriptions to avoid unnecessary usage of memory due to its content.

        for d_categories in data['categories']:
            if d_categories['name'] in l_CategoryNames:
                del d_categories['description']
                l_categories.append(d_categories)
                logger.debug("List of categories: '{}'".format("category_name: " + d_categories['name'].encode('ascii', 'ignore')))
                logger.debug("List of categories: '{}'".format("category_id: " + str(d_categories['id'])))

        # Increment page

        v_currentpage += 1
        logger.debug("Incremented categories pages count: '{}'".format(v_currentpage))

    # Return the list to be used by the program fn_get_articles_info()

    return l_categories


# Step 5:
# Function : fn_get_articles_info(categories_id,categories_name)
# It uses the category ID that was provided by fn_get_categories_id()
# and then pulls the articles all of them on those categories and then stores it onto the list


def fn_get_articles_info(categories_id,categories_name):

    # Local Variables

    l_articles = []
    v_currentpage = 1
    logger.debug("Sub categories current page: '{}'".format(v_currentpage))
    headers = {'Content-Type': 'application/json'}

    # Get the API for sub categories from the d_zdapi mentioned above
    # Including the translation to obtain the actual updated time rather than metadata updated date.

    v_pageurl = d_zdapi['sub_catergories'].format(id=str(categories_id)) + "?include=translations"
    logger.debug("Sub categories page url: '{}'".format(v_pageurl))

    # Get the max number of pages on the URL, so that we can crawl till the end of the page.

    v_maxpage = fn_get_page_count(v_pageurl)
    logger.info("Sub categories max pages: '{}'".format(v_maxpage))

    # Loop till we reach the end of the page.

    while v_currentpage <= v_maxpage:

        # The URL changes on every page , the below parameter makes those adjustment

        v_pageurlincrement = v_pageurl + "&page=" + str(v_currentpage)
        logger.info("Reading Sub categories URL: '{}'".format(v_pageurlincrement))

        # Get the data from the url page

        response = zd.get(v_pageurlincrement, headers=headers)
        data = response.json()
        # print (fn_json_formatter((data)))

        # Loop through the data obtained from the API
        # We append all the dictionary information onto a list, during this process we add
        # the category_id and category_name also to the list so that its easy to divide by section,
        # and also changes the date from JSON format to more readable format.

        for d_articles in data['articles']:
            d_articles['category_id'] = categories_id
            d_articles['category_name'] = categories_name
            v_modifycreatetime = dateutil.parser.parse(d_articles['created_at'])

            # NOTE: Zendesk JSON has two "updated_at" field, the main updated_at is the time when the metadata
            # was updated (which is of no interest to us) and other inside translation dictionary tells
            # when the documents was changed or re-translated from original content which makes more sense.

            for v_updateddate in d_articles['translations']:
                v_modifyupdatetime = dateutil.parser.parse(v_updateddate['updated_at'])
                del v_updateddate['body']

            del d_articles['body']
            d_articles['created_at'] = str(v_modifycreatetime)
            d_articles['updated_at'] = str(v_modifyupdatetime)
            l_articles.append(d_articles)
            logger.debug("List of sub categories: '{}'".format("category_name: " + d_articles['category_name'].encode('ascii', 'ignore')))
            logger.debug("List of sub categories: '{}'".format("category_id: " + str(d_articles['category_id'])))
            logger.debug("List of sub categories: '{}'".format("article_name: " + d_articles['name'].encode('ascii', 'ignore')))
            logger.debug("List of sub categories: '{}'".format("article_url: " + d_articles['html_url']))
            logger.debug("List of sub categories: '{}'".format("article_created: " + str(d_articles['created_at'])))
            logger.debug("List of sub categories: '{}'".format("article_updated: " + str(d_articles['updated_at'])))

        # Increment page

        v_currentpage += 1
        logger.debug("Incremented sub categories pages count: '{}'".format(v_currentpage))

    # Return the list to be used by rest of the program in the main() block

    return l_articles


# Step 6:
# Function : main()
# The main function
# It loops to find the articles under different categories that has been modified in the last 7 days.


def main():

    # Start program message

    logger.info("Start of the program: '{}'".format(__file__))

    # Local parameters that is used by this function

    l_articles = []
    l_updatedarticles = []

    # Obtain the current and last week date & time

    v_currenttime = datetime.datetime.now()
    v_lastweekdate = (v_currenttime - timedelta(days=v_CheckDays))
    logger.debug("Days(past) report requested: '{}'".format(v_CheckDays))
    logger.info("Get Current date & time: '{}'".format(v_currenttime))
    logger.info("Get LastWeek date & time: '{}'".format(v_lastweekdate))

    # Call the function to obtain the category ID's

    logger.info("Start of the function to gather the categories ID")

    d_categoryfinal = fn_get_categories_id()

    logger.debug("End of the function to gather the categories ID")

    # Call the function fn_get_articles_info() to obtain the updated articles in the category obtained above

    logger.info("Start of the function to gather the articles in category")

    for d_category_id in d_categoryfinal:
        logger.info("Pull data for category: '{}'".format(d_category_id['name'].encode('ascii', 'ignore')))
        l_articles += fn_get_articles_info(d_category_id['id'],d_category_id['name'])
        logger.debug("End pulling data from category: '{}'".format(d_category_id['name'].encode('ascii', 'ignore')))

    logger.debug("End of the function to gather the articles in category")

    # Change the time from JSON time format to much more readable and obtain the last week articles.

    logger.info("Selecting articles that was published / updated in last week")

    for d_article in l_articles:
        if datetime.datetime.strptime(d_article['updated_at'][:19],'%Y-%m-%d %H:%M:%S') > v_lastweekdate:
            l_updatedarticles.append(d_article)
            logger.debug("List of last week article: '{}'".format("category_name: " + d_article['category_name'].encode('ascii', 'ignore')))
            logger.debug("List of last week article: '{}'".format("category_id: " + str(d_article['category_id'])))
            logger.debug("List of last week article: '{}'".format("article_name: " + d_article['name'].encode('ascii', 'ignore')))
            logger.debug("List of last week article: '{}'".format("article_url: " + d_article['html_url']))
            logger.debug("List of last week article: '{}'".format("article_created: " + str(d_article['created_at'])))
            logger.debug("List of last week article: '{}'".format("article_updated: " + str(d_article['updated_at'])))

    logger.debug("Finished selecting articles that was published / updated in last week")

    # Sort the article list so that we can divide the article into section by Jinja2 Framework

    logger.debug("Sorting articles based on category")
    l_sortedarticles = sorted(l_updatedarticles, key=itemgetter('category_name'))

    # The below set of line is to use jinja2 framework
    # The sorted list obtained above is changed into HTML tags and written to a file
    # The template used by the framework is "articles.html"

    logger.info("Creating HTML tags for the information gathered")

    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    templateFile = "articles.html"
    template = templateEnv.get_template(templateFile)
    v_outputtext = template.render({
        'articles': l_sortedarticles,
        'v_current_time': v_currenttime,
        'v_last_week_date': v_lastweekdate
    })

    # Write all the information on to a file to debug or audit if any issues

    fn_write_to_file(v_outputtext)

    # Sending email
    # Check if there is content or not before sending email
    # The values of 67 was obtained after checking total words without content under "v_outputtext"

    logger.debug("Checking the content exists: '{}'".format(len(v_outputtext.split())))
    if len(v_outputtext.split()) <= 67:

        # No content, send the below html code as email

        html = str("""\
        <html>
        <head></head>
        <h2 align="center"><font face="verdana"> """ +
           ("Article published / updated from \"{0}\" to \"{1}\" </font></h2>".format(v_lastweekdate,v_currenttime)) +
        """<body>
        <p></p>
        <p><font face="verdana"> No new articles published / updated past """ + str(v_CheckDays) + """ day.
        </font></p>
        <p></p>
        </body>
        </html>
        """)

        fn_send_email(html)

    else:

        # Content available, send the content as email

        fn_send_email(v_outputtext)

    # End program message

    logger.info("End of the program: '{}'".format(__file__))


# Step 7
# Call the main function and start the program


main()

# -*- coding: utf-8 -*-

#############################################################################################
#                                 Python program                                            #
#                       Written with python code version 2.7                                #
#                                                                                           #
# The Program does the below task                                                           #
#                                                                                           #
#   + Get all the categories in the zendesk                                                 #
#   + Get all the articles in the category                                                  #
#   + Get all the Agent users information                                                   #
#   + Plot graph for all the articles created per month                                     #
#   + Plot graph for all the articles created per category for last month                   #
#   + Plot graph for top contributors for last month                                        #
#   + Plot graph for articles in draft mode                                                 #
#   + Plot graph for articles in knowledge base and for review                              #
#   + Plot graph for overall total articles per category                                    #
#   + Plot graph for overall contributors to the knowledge base                             #
#                                                                                           #
# Naming convention used:                                                                   #
#   fn_ = function   ,  v_ = variable                                                       #
#    l_ = list       ,  d_ = dictionary                                                     #
#                                                                                           #
#############################################################################################


# Importing modules needed for the program
# If the import modules fail then install using "pip install <module-name>"
# For Python 2.6, IPython fails when installing with pip
# Install manually using "https://ipython.org/ipython-doc/2/install/install.html"

import requests
import json
import dateutil.parser
import datetime
import logging
from operator import itemgetter
from dateutil.relativedelta import relativedelta
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import collections
import sys, getopt
import plotly.plotly as py
import plotly.graph_objs as go
from plotly.graph_objs import *
from IPython.display import display, HTML

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


username = "username"
password = "password"


# Authenticate the username / password here and set it globally
# This authentications is used by the functions fn_get_categories_id() & fn_get_articles_info()


zd = requests.session()
zd.auth = (username, password)

# Global Functions

# Function : fn_json_formatter
# This function is not important as it has been commented out at most places
# This is used to format the json output to better understand the json output ( for debugging )


def fn_json_formatter(jsondata):

    jsonformatter = json.dumps(
            jsondata,
            indent=4,
            sort_keys=True
    )

    print (jsonformatter)


# Function : fn_get_page_count
# Picks up the total pages under a url, this can be used to increment the web crawling


def fn_get_page_count(url):

    headers = {
        'Content-Type': 'application/json'
    }

    response = zd.get(
            url,
            headers=headers
    )

    data = response.json()

    return data['page_count']

# Step 1:
# Get all the zendesk API , its manual and this is obtained from
# https://developer.zendesk.com/rest_api/docs/help_center/articles


v_top_level_url = "https://discuss.zendesk.com"

d_zdapi = {
"users" : v_top_level_url + "/api/v2/users.json",
"categories" : v_top_level_url + "/api/v2/help_center/en-us/categories.json",
"sub_catergories" : v_top_level_url + "/api/v2/help_center/categories/{id}/articles.json",
"sections" : v_top_level_url + "/api/v2/help_center/categories/{id}/sections.json"
}

# Step 2:
# Create a list of category that you need further check
# Here we are interested in knowing how much articles are under review
# The category is called "knowledge space", so placing this under a list.

l_CategoryName = [
    "Knowledge Space"
]

# Step 3:
# Function : fn_UserInfo
# This function loops into the Zendesk API to find all the users list that are agents.
# We then store all those users dictionary on a single list

def fn_UserInfo():

    # Local variables

    l_users = []
    v_currentpage = 1
    logger.debug("User list current page: '{}'".format(v_currentpage))
    headers = {'Content-Type': 'application/json'}

    # Get the API for categories from the d_zdapi mentioned above

    v_pageurl = d_zdapi['users']
    logger.debug("Users URL: '{}'".format(v_pageurl))

    # The URL changes on every page , the below parameter makes those adjustment

    v_pageurlincrement = v_pageurl + "?page=" + str(v_currentpage)
    logger.info("Reading Users list URL: '{}'".format(v_pageurlincrement))

    # Loop till we reach the end of the page.

    while v_pageurlincrement != None:

        # Get the data from the url page

        response = zd.get(v_pageurlincrement, headers=headers)
        data = response.json()
        # print (fn_json_formatter((data)))

        # Loop through the data obtained from the API
        # and just pick the information we are interested (i.e only agents) and append it to the list

        for d_users in data['users']:
            if d_users['role'] == "agent":
                l_users.append(d_users)
                logger.debug("List of Users: '{}'".format("user_name: " + d_users['name'].encode('ascii', 'ignore')))
                logger.debug("List of Users: '{}'".format("user_id: " + str(d_users['id'])))

        # Increment page

        v_pageurlincrement = data['next_page']
        logger.info("Reading User list URL: '{}'".format(v_pageurlincrement))

    # Return the list to be used by the rest of the program

    return l_users

# Step 4:
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

        # Loop through the data obtained from the API and pick the necessary info
        # we delete descriptions to avoid unnecessary usage of memory due to its content.

        for d_categories in data['categories']:
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

    v_pageurl = d_zdapi['sub_catergories'].format(id=str(categories_id))
    logger.debug("Sub categories page url: '{}'".format(v_pageurl))

    # Get the max number of pages on the URL, so that we can crawl till the end of the page.

    v_maxpage = fn_get_page_count(v_pageurl)
    logger.info("Sub categories max pages: '{}'".format(v_maxpage))

    # Loop till we reach the end of the page.

    while v_currentpage <= v_maxpage:

        # The URL changes on every page , the below parameter makes those adjustment

        v_pageurlincrement = v_pageurl + "?page=" + str(v_currentpage)
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

            del d_articles['body']
            d_articles['created_at'] = str(v_modifycreatetime)
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
# Function : fn_PlotOverallContributors()
# The below function calculate the total articles per author

def fn_getSectionName(categories_id,categories_name):

    l_sections = []
    v_currentpage = 1
    logger.debug("Section current page: '{}'".format(v_currentpage))
    headers = {'Content-Type': 'application/json'}

    # Get the API for sections from the d_zdapi mentioned above

    v_pageurl = d_zdapi['sections'].format(id=str(categories_id))
    logger.debug("Section page url: '{}'".format(v_pageurl))

    # Get the max number of pages on the URL, so that we can crawl till the end of the page.

    v_maxpage = fn_get_page_count(v_pageurl)
    logger.info("Section max pages: '{}'".format(v_maxpage))

    # Loop till we reach the end of the page.

    while v_currentpage <= v_maxpage:

        # The URL changes on every page , the below parameter makes those adjustment

        v_pageurlincrement = v_pageurl + "?page=" + str(v_currentpage)
        logger.info("Section categories URL: '{}'".format(v_pageurlincrement))

        # Get the data from the url page

        response = zd.get(v_pageurlincrement, headers=headers)
        data = response.json()
        # print (fn_json_formatter((data)))

        # Loop through the data obtained from the API
        # We append all the dictionary information onto a list, during this process we add
        # the category_id and category_name also to the list so that its easy to divide by section

        for d_sections in data['sections']:
            d_sections['category_id'] = categories_id
            d_sections['category_name'] = categories_name
            l_sections.append(d_sections)
            logger.debug("List of section: '{}'".format("category_id: " + str(d_sections['category_id'])))
            logger.debug("List of section: '{}'".format("category_name: " + d_sections['category_name'].encode('ascii', 'ignore')))
            logger.debug("List of section: '{}'".format("section_id: " + str(d_sections['id'])))
            logger.debug("List of section: '{}'".format("section_name: " + d_sections['name'].encode('ascii', 'ignore')))
        # Increment page

        v_currentpage += 1
        logger.debug("Incremented section pages count: '{}'".format(v_currentpage))

    # Return the list to be used by rest of the program in the main() block

    return l_sections


# Step 6:
# Function : fn_PlotOverallTopContributors()
# The below function calculate the overall total articles per author

def fn_PlotOverallTopContributors(l_articles, d_UserList):

    # Local variables

    d_AuthorOccurance = {}
    d_TotalOccurance = {}
    x_plot = []
    y_plot = []

    # Count the number of articles created by a Author

    for d_Author in l_articles:
        Total = d_Author['author_id']
        if Total not in d_AuthorOccurance:
            d_AuthorOccurance[Total] = 0
        if Total in d_AuthorOccurance:
            d_AuthorOccurance[Total] += 1

    logger.debug("Overall KB Contributors: '{}'".format(d_AuthorOccurance))

    # Map the Author's Id with the Author's name from the list obtained above

    for key, value in d_AuthorOccurance.items():
        for v_Author in d_UserList:
            if v_Author['id'] == key:
               d_TotalOccurance[v_Author['name']] = value

    logger.debug("Overall KB Contributors name: '{}'".format(d_TotalOccurance))

    # Sort the list based on the highest contributors and select the Top 10

    Top10OverallContributors = dict(sorted(d_TotalOccurance.items(), key=itemgetter(1), reverse=True)[:10])

    logger.debug("Overall Top 10 KB Contributors: '{}'".format(Top10OverallContributors))

    # Select the key and value from the sorted list and separate them with x and y so that we can plot on the graph

    for key,value in Top10OverallContributors.items():
        x_plot.append(key)
        y_plot.append(value)

    data = [
    go.Bar(
        y=y_plot,
        x=x_plot
        )
    ]

    layout = go.Layout(
            title='Overall Top 10 KB Contributors',
            font = dict(
                    size=8,
                    color='#7f7f7f'
            ),
            titlefont = dict(
                    size = 20
            ),
            height = 608,
            width = 1188,
            autosize = 'true',
            xaxis=dict(
                    title='Contributors',
                    titlefont=dict(
                            size=18,
                            color='#7f7f7f'
                    )
            ),
            yaxis=dict(
                    title='Total Articles',
                    titlefont=dict(
                            size=18,
                            color='#7f7f7f'
                    )
            )
    )

    fig = go.Figure(
            data=data,
            layout=layout
    )

    url_OverallContributor = py.plot(
            fig,
            filename='Overall-Top-10-Contributors'
    )

    logger.debug("Overall KB Contributors hosted URL: '{}'".format(
            url_OverallContributor
    ))

    return url_OverallContributor


# Step 7:
# Function : fn_PlotTotalArticlePerCategory()
# The below function calculate total articles per category and also separate the count
# based on articles if its publised or its on draft.

def fn_PlotOverallTotalArticlePerCategory(l_articles):

    # Local variables

    d_CategoryOccurance = {}
    d_DraftArticles = {}
    d_NonDraftArticles = {}
    x1_plot = []
    y1_plot = []
    y2_plot = []
    y3_plot = []

    # Count the Total number of articles by category and separate them with Published and in Draft mode.

    for d_category in l_articles:

        Total = d_category['category_name']

        if Total not in d_CategoryOccurance:
            d_CategoryOccurance[Total] = 0

        if Total not in d_DraftArticles:
            d_DraftArticles[Total] = 0

        if Total not in d_NonDraftArticles:
            d_NonDraftArticles[Total] = 0

        if Total in d_CategoryOccurance:
            d_CategoryOccurance[Total] += 1
            if d_category['draft'] == True:
                    d_DraftArticles[Total] += 1
            if d_category['draft'] == False:
                    d_NonDraftArticles[Total] += 1

    logger.debug("Overall Total Articles per Category: '{}'".format(d_CategoryOccurance))
    logger.debug("Overall Total Articles in Draft per Category: '{}'".format(d_DraftArticles))
    logger.debug("Overall Total Articles  per Published Category: '{}'".format(d_NonDraftArticles))

    od = collections.OrderedDict(
            sorted(
                    d_CategoryOccurance.items(),
                    key=itemgetter(1),
                    reverse=True
            )
    )

    # Select the key and value from the sorted list and separate them with x and y so that we can plot on the graph

    for key, value in od.items():
        x1_plot.append(key)
        y1_plot.append(value)

    for key_l in x1_plot:
        for key,value in d_DraftArticles.items():
            if key == key_l:
                y2_plot.append(value)

    for key_l in x1_plot:
        for key,value in d_NonDraftArticles.items():
            if key == key_l:
                y3_plot.append(value)

    trace0 = go.Scatter(
            x=x1_plot,
            y=y1_plot,
            mode= 'lines+markers',
            name='Total Articles',
            fillcolor = "rgba(238, 238, 238, 0)"
    )

    trace1 = go.Scatter(
            x=x1_plot,
            y=y3_plot,
            mode= 'lines+markers',
            name='Published',
            fillcolor = "rgba(238, 238, 238, 0)"
    )

    trace2 = go.Scatter(
            x=x1_plot,
            y=y2_plot,
            mode= 'lines+markers',
            name='Draft',
            fillcolor = "rgba(238, 238, 238, 0)"
    )

    data = [
        trace0,
        trace1,
        trace2
    ]

    layout = go.Layout(
        title='Overall Total KB Articles per category',
        font = dict(
                size=8,
                color='#7f7f7f'

        ),
        titlefont = dict(
                size = 20
        ),
        xaxis=dict(
                type = "Category",
                range = [0,29],
                title='Category',
                autorange = 'true',
                titlefont=dict(
                        size=18,
                        color='#7f7f7f'
                ),
        ),
        yaxis=dict(
                type = "linear",
                title='Total Articles',
                autorange = 'true',
                titlefont=dict(
                size=18,
                color='#7f7f7f'
                ),
        ),
        height = 608,
        width = 1188,
        autosize = 'true',
        margin = dict(
                l = 80,
                r = 80,
                b = 130
        ),
    )

    fig = go.Figure(
            data=data,
            layout=layout
    )

    url_OverallTotalArticlePerCategory = py.plot(
            fig,
            filename='Overall-Articles-Per-Category'
    )

    logger.debug("Overall Total Article per category hosted URL: '{}'".format(
            url_OverallTotalArticlePerCategory
    ))

    return url_OverallTotalArticlePerCategory


# Step 8:
# Function : fn_PlotTotalArticlesPerMonth()
# The below function calculate total articles per category and also separate the count
# based on articles if its published or its on draft.


def fn_PlotTotalArticlesPerMonth(l_articles):

    # Local Variables

    v_HowManyMonths = -13
    l_Months = []
    d_ArticlesPerMonth = {}
    x_plot=[]
    y_plot=[]

    # Get the last 12 months dates

    while v_HowManyMonths <= -1:
        v_TodaysDate = datetime.date.today() + relativedelta(months=v_HowManyMonths)
        v_Months = datetime.date.strftime(v_TodaysDate,"%Y-%m")
        l_Months.append(v_Months)
        v_HowManyMonths += 1

    logger.debug("12 Months list: '{}'".format(l_Months))

    # Get the total occurance of article per month.

    for Months in l_Months:
        for d_category in l_articles:
            if d_category['created_at'][:7] == str(Months):
                Total = d_category['created_at'][:7]
                if Total not in d_ArticlesPerMonth:
                    d_ArticlesPerMonth[Total] = 0
                if Total in d_ArticlesPerMonth:
                    d_ArticlesPerMonth[Total] += 1

    logger.debug("Total Article created for last 12 Month: '{}'".format(d_ArticlesPerMonth))

    # Sort the key to get in a ordered list.

    for key in sorted(d_ArticlesPerMonth):
        x_plot.append(key)
        y_plot.append(d_ArticlesPerMonth[key])

    # Plot the values on the grpah

    data = [
        go.Scatter(
        y=y_plot,
        x=x_plot
        )
    ]

    layout = go.Layout(
            title='Total KB Contributed in Last 12 Months',
            font = dict(
            size=8,
            color='#7f7f7f'
            ),
            titlefont = dict(
            size = 20
            ),
            height = 608,
            width = 1188,
            autosize = 'true',
            xaxis=dict(
                    autorange=True,
                    nticks=21,
                    title='Months',
                    titlefont=dict(
                            size=18,
                            color='#7f7f7f'
                    ),
                    type='date'
            ),
            yaxis=dict(
                    autorange=True,
                    nticks=21,
                    title='Total Articles',
                    titlefont=dict(
                    size=18,
                    color='#7f7f7f'
                    ),
                    type='linear'
            )
    )

    fig = go.Figure(
            data=data,
            layout=layout
    )

    url_TotalArticlesPerMonth = py.plot(
            fig,
            filename='total-article-12-months'
    )

    logger.debug("Total Article for last 12 Months hosted URL: '{}'".format(
            url_TotalArticlesPerMonth
    ))

    return url_TotalArticlesPerMonth


# Step 9:
# Function : fn_PlotTotalArticlesPerMonth()
# The below function calculate total articles per category and also separate the count
# based on articles if its published or its on draft.


def fn_PlotArticleUnderKMSections(l_articles, l_sections):

    # Local Variables

    d_ArticlesPerKMSection = {
        "KM Review": 0,
        "SME Review": 0,
        "First Draft": 0
    }
    x_plot=[]
    y_plot=[]

    # Get the total articles under different section of KM review process.

    for d_sections in l_sections:
        for d_category in l_articles:
            if d_sections['id'] == d_category['section_id']:
                Total = d_sections['name']
                if Total not in d_ArticlesPerKMSection:
                    d_ArticlesPerKMSection[Total] = 0
                if Total in d_ArticlesPerKMSection:
                    d_ArticlesPerKMSection[Total] += 1

    logger.debug("Total Article in KM Review: '{}'".format(d_ArticlesPerKMSection))

    # Plot the values on Pie Chart.

    for key, value in d_ArticlesPerKMSection.items():
        x_plot.append(key)
        y_plot.append(value)

    data = Data([
        Pie(
                direction='counterclockwise',
                domain=dict(
                        x=[0]
                ),
                hole=0,
                labels=x_plot,
                marker=Marker(
                        line=Line(
                                width=1
                        )
                ),
                name='y',
                opacity=0.84,
                pull=0,
                sort=True,
                textfont=dict(
                        color='rgb(0, 0, 0)',
                        size=36
                ),
                textinfo='value',
                textposition='auto',
                values=y_plot,
        )
    ])

    layout = Layout(
            autosize=True,
            font=Font(
                    color='#7f7f7f',
                    size=8
            ),
            height=1146,
            title='Total KB currently under KB Reviewer\'s Queue',
            titlefont=dict(
                    size=20
            ),
            width=1220
    )

    fig = Figure(
            data=data,
            layout=layout
    )

    url_TotalArticleUnderKMSection = py.plot(
            fig,
            filename='Total-Article-Under-KM-Review'
    )

    logger.debug("Total Article under KM Section hosted URL: '{}'".format(
            url_TotalArticleUnderKMSection
    ))

    return url_TotalArticleUnderKMSection


# Step 9:
# Function : fn_PlotTotalArticlesPerMonth()
# The below function calculate total articles per category for last month


def fn_PlotTotalArticleforMonthPerCategory(l_articles):

    # Local Variables

    v_TodaysDate = datetime.date.today()
    v_LastMonthDate = v_TodaysDate + relativedelta(months=-1)
    v_Months = datetime.date.strftime(v_LastMonthDate,"%Y-%m")
    d_ArticlesForMonthPerCategory = {}
    x_plot = []
    y_plot = []

    # Loop through the article list to get the number of occurance of a category last month

    for d_category in l_articles:
            if d_category['created_at'][:7] == str(v_Months) and d_category['category_name'] not in l_CategoryName:
                Total = d_category['category_name']
                if Total not in d_ArticlesForMonthPerCategory:
                    d_ArticlesForMonthPerCategory[Total] = 0
                if Total in d_ArticlesForMonthPerCategory:
                    d_ArticlesForMonthPerCategory[Total] += 1

    logger.debug("Total Article Per Category for Last Month: '{}'".format(d_ArticlesForMonthPerCategory))

    # Get the values and plot that on a graph

    for key, value in d_ArticlesForMonthPerCategory.items():
        x_plot.append(key)
        y_plot.append(value)

    trace = go.Scatter(
        x=x_plot,
        y=y_plot,
        mode= 'lines+markers',
        fillcolor = "rgba(238, 238, 238, 0)",
        name = "values",
        visible = 'true',
        hoverinfo = "all",
            line = dict (
                    dash = "dot",
                    width = 2,
                    shape = "spline"
            ),
        marker = dict(
                symbol = "circle",
                maxdisplayed = 0,
                size = 6
        ),
    )

    layout = go.Layout(
            title='Category with the Highest KB Contribution Last Month',
            font = dict(
                    size=8,
                    color='#7f7f7f'

            ),
            titlefont = dict(
                    size = 20
            ),
            xaxis=dict(
                    type = "Category",
                    title='Category',
                    autorange = 'true',
                    titlefont=dict(
                            size=18,
                            color='#7f7f7f'
                    ),
            ),
            yaxis=dict(
                    type = "linear",
                    title='Total Articles',
                    autorange = 'true',
                    titlefont=dict(
                    size=18,
                    color='#7f7f7f'
                    ),
            ),
            height = 608,
            width = 1188,
            autosize = 'true',
            margin = dict(
                    pad = 1,
                    autoexpand = 'true',
                    b = 130
            ),
    )

    data = [trace]

    fig = go.Figure(
            data=data,
            layout=layout
    )

    url_HighestContributedCategoryLastMonth = py.plot(
            fig,
            filename='Category-with-highest-contribution-last-month'
    )

    logger.debug("Total Article Per Category for Last Month hosted URL: '{}'".format(
            url_HighestContributedCategoryLastMonth
    ))

    return url_HighestContributedCategoryLastMonth


# Step 10:
# Function : fn_PlotTotalArticlesPerMonth()
# The below function calculate total articles per category and also separate the count
# based on articles if its published or its on draft.


def fn_PlotTotalArticleforMonthPerAuthor(l_articles, d_UserList):

    # Local Variables

    v_TodaysDate = datetime.date.today()
    v_LastMonthDate = v_TodaysDate + relativedelta(months=-1)
    v_Months = datetime.date.strftime(v_LastMonthDate,"%Y-%m")
    d_ArticlesForMonthPerAuthor = {}
    d_ArticlesForMonthPerAuthorName = {}
    x_plot = []
    y_plot = []

    # Get the list of articles and count the occurance of the author in the last month

    for d_category in l_articles:
            if d_category['created_at'][:7] == str(v_Months):
                Total = d_category['author_id']
                if Total not in d_ArticlesForMonthPerAuthor:
                    d_ArticlesForMonthPerAuthor[Total] = 0
                if Total in d_ArticlesForMonthPerAuthor:
                    d_ArticlesForMonthPerAuthor[Total] += 1

    for key, value in d_ArticlesForMonthPerAuthor.items():
        for v_Author in d_UserList:
            if v_Author['id'] == key:
                d_ArticlesForMonthPerAuthorName[v_Author['name']] = value

    Top10OLastMonthContributor = dict(sorted(d_ArticlesForMonthPerAuthorName.items(), key=itemgetter(1), reverse=True))

    logger.debug("Total Article Per Author for the month: '{}'".format(Top10OLastMonthContributor))

    # Use the value and plot them to the graph.

    for key, value in Top10OLastMonthContributor.items():
        x_plot.append(key)
        y_plot.append(value)

    data = [
        go.Bar(
                y=x_plot,
                x=y_plot,
                marker=Marker(
                        line=Line(
                                color='rgb(255, 0, 0)'
                        )
                ),
                orientation='h'
        )
    ]

    layout = go.Layout(
            title='KB Contributors for Last Month',
            font = dict(
                    size=8,
                    color='#7f7f7f'
            ),
            titlefont = dict(
            size = 20
            ),
            height = 608,
            width = 1188,
            margin=Margin(
                l=110
            ),
            autosize = 'true',
            xaxis=dict(
                    title='Total Articles',
                    titlefont=dict(
                            size=18,
                            color='#7f7f7f'
                    )
            ),
            yaxis=dict(
                    title='Contributors',
                    titlefont=dict(
                            size=18,
                            color='#7f7f7f'
                    )
            )
    )

    fig = go.Figure(
            data=data,
            layout=layout
    )

    url_ArticlesForMonthPerAuthorName = py.plot(
            fig,
            filename='KB-Top-Contibutors-Last-Month'
    )

    logger.debug("Total Article contributed by Author for Last Month Hosted URL: '{}'".format(
            url_ArticlesForMonthPerAuthorName
    ))

    return url_ArticlesForMonthPerAuthorName

# Step 11:
# Function : fn_PlotTotalArticlesPerMonth()
# The below function calculate total articles per category and also separate the count
# based on articles if its published or its on draft.


def fn_PlotDraftArticlePerYear(l_articles):

    # Local Variables

    v_TodaysDate = datetime.datetime.now()
    v_LastWeekDate = v_TodaysDate + relativedelta(weeks=-1)
    v_LastMonthDate = v_TodaysDate + relativedelta(months=-1)
    v_ThreeMonthDate = v_TodaysDate + relativedelta(months=-3)
    d_DraftArticle = collections.OrderedDict()
    d_DraftArticle['Less than a week'] = 0
    d_DraftArticle['Less than a month'] = 0
    d_DraftArticle['Less than 3 months'] = 0
    d_DraftArticle['More than 3 months'] = 0
    x_plot = []
    y_plot = []

    # From the list of article pick the draft once and increment then based on number days it was open

    for d_category in l_articles:
        v_stringtodate = datetime.datetime.strptime(d_category['created_at'][:10], '%Y-%m-%d')
        if v_stringtodate >= v_LastWeekDate and v_stringtodate < v_TodaysDate and d_category['draft'] == True:
            Total = "Less than a week"
            if Total in d_DraftArticle:
                d_DraftArticle[Total] += 1

        if v_stringtodate >= v_LastMonthDate and v_stringtodate < v_LastWeekDate and d_category['draft'] == True:
            Total = "Less than a month"
            if Total in d_DraftArticle:
                d_DraftArticle[Total] += 1

        if v_stringtodate >= v_ThreeMonthDate and v_stringtodate < v_LastMonthDate and d_category['draft'] == True:
            Total = "Less than 3 months"
            if Total in d_DraftArticle:
                d_DraftArticle[Total] += 1

        if v_stringtodate < v_LastMonthDate and d_category['draft'] == True:
            Total = "More than 3 months"
            if Total in d_DraftArticle:
                d_DraftArticle[Total] += 1

    logger.debug("Total Article in Draft mode: '{}'".format(d_DraftArticle))

    # Plot the values in the graph

    for key, value in d_DraftArticle.items():
        x_plot.append(key)
        y_plot.append(value)

    data = Data(
            [
                Pie(
                        hole=0.5,
                        direction='clockwise',
                        hoverinfo='all',
                        labels=x_plot,
                        rotation=180,
                        sort=False,
                        marker=Marker(
                                line=Line(
                                        width=2
                                )
                        ),
                        name='values',
                        opacity=0.84,
                        pull=0.009,
                        showlegend=True,
                        textfont=dict(
                                color='rgb(0, 0, 0)',
                                size=16
                        ),
                        textinfo='value',
                        values=y_plot,
                        visible=True
                )
            ]
    )
    layout = Layout(
            autosize=True,
            barmode='overlay',
            font=Font(
                    color='#7f7f7f',
                    size=8
            ),
            height=1146,
            margin=Margin(
                    autoexpand='true',
                    b=130,
                    pad=1
            ),
            title='KB Articles in Draft Mode',
            titlefont=dict(
                    size=20
            ),
            width=1220
    )

    fig = Figure(
            data=data,
            layout=layout
    )

    url_PlotDraftArticle = py.plot(
            fig,
            filename='KB-Articles-in-draft-mode'
    )

    logger.debug("Total Article in Draft by days Hosted URL: '{}'".format(
            url_PlotDraftArticle
    ))

    return url_PlotDraftArticle


# Step 12:
# Function : main()
# The main function


def main():

    # Start program message

    logger.info("Start of the program: '{}'".format(__file__))

    # Local parameters that is used by this function

    l_articles = []
    d_UserCount = {}

    # Obtain the current date & time

    v_currenttime = datetime.datetime.now()
    v_LastMonth = v_currenttime + relativedelta(months=-1)
    logger.info("Get Current date & time: '{}'".format(v_currenttime))
    logger.info("Get Last Month: '{}'".format(v_LastMonth.strftime('%b %Y')))

    # Call the function to obtain the category ID's

    logger.info("Start of the function to gather the categories ID")

    l_category = fn_get_categories_id()

    logger.debug("End of the function to gather the categories ID")

    # Call the function fn_get_articles_info() to obtain the articles in the category obtained above

    logger.info("Start of the function to gather the articles in category")

    for d_category_id in l_category:
        logger.info("Pull data for category: '{}'".format(d_category_id['name'].encode('ascii', 'ignore')))
        l_articles += fn_get_articles_info(
                d_category_id['id'],
                d_category_id['name']
        )

        # For the category inside the l_categoryName get the section name as well

        if d_category_id['name'] in l_CategoryName:
            logger.info("Pull data for section: '{}'".format(d_category_id['name'].encode('ascii', 'ignore')))
            l_sections = fn_getSectionName(
                    d_category_id['id'],
                    d_category_id['name']
            )
            logger.debug("End pulling data from section: '{}'".format(d_category_id['name'].encode('ascii', 'ignore')))

        logger.debug("End pulling data for category: '{}'".format(d_category_id['name'].encode('ascii', 'ignore')))

    logger.debug("End of the function to gather the articles in category")

    # Get all the agent Users Information

    logger.info("Start of the function to gather the agent User Information")

    l_UserList = fn_UserInfo()

    logger.debug("End of the function to gather the agent User Information")

    # Plot the graph for the Total Articles per Month.

    logger.info("Start of the function to gather the Total articles per Month")

    v_TotalArticlePerMonth = fn_PlotTotalArticlesPerMonth(
            l_articles
    )

    logger.debug("End of the function to gather the Total articles per Month")

    # Plot the graph for the Total Articles per Month per Category.

    logger.info("Start of the function to gather the Total Articles for Last Month per Category")

    v_TotalArticleforLastMonthPerCategory = fn_PlotTotalArticleforMonthPerCategory(
            l_articles
    )

    logger.debug("End of the function to gather the Total Articles for Last Month per Category")

    # Plot the graph for the Total Articles per Month per Author.

    logger.info("Start of the function to gather the Total Articles for Month per Author")

    v_TotalArticleforMonthPerAuthor = fn_PlotTotalArticleforMonthPerAuthor(
            l_articles,
            l_UserList
    )

    logger.debug("End of the function to gather the Total Articles for Month per Author")

    # Plot the graph for the Total Articles in Draft Mode.

    logger.info("Start of the function to gather the Total Articles in Draft Mode")

    v_DraftArticlePerYear = fn_PlotDraftArticlePerYear(
            l_articles
    )

    logger.debug("End of the function to gather the Total Articles in Draft Mode")

    # Plot the graph for the Total Articles per category.

    logger.info("Start of the function to gather the Overall Total articles per category")

    v_OverallTotalArticlePerCategory = fn_PlotOverallTotalArticlePerCategory(
            l_articles
    )

    logger.debug("End of the function to gather the Overall Total articles per category")

    # Plot the graph for the Total Article Under KM Section.

    logger.info("Start of the function to gather Total Article Under KM Section")

    v_TotalArticlePerKMSection = fn_PlotArticleUnderKMSections(
            l_articles,
            l_sections
    )

    logger.debug("End of the function to gather  Total Article Under KM Section")

    # Plot the graph for the overall top 10 KB contributors.

    logger.info("Start of the function to gather the Overall Top 10 KB Contributors")

    v_Top10OverallTopContributor = fn_PlotOverallTopContributors(
            l_articles,
            l_UserList
    )

    logger.debug("End of the function to gather the Overall Top 10 KB Contributors")

    # All the url to where the graph is plotted.

    graphs = [
        v_TotalArticlePerMonth,
        v_TotalArticleforLastMonthPerCategory,
        v_TotalArticleforMonthPerAuthor,
        v_DraftArticlePerYear,
        v_TotalArticlePerKMSection,
        v_OverallTotalArticlePerCategory,
        v_Top10OverallTopContributor
    ]

    # Template for the email body
    # Open the interactive graph when you click on the image
    # Use the ".png" magic url so that the latest, most-up-to-date image is included

    template = (''
        '<a href="{graph_url}" target="_blank">'
            '<img src="{graph_url}.png">'
        '</a>'
        '{caption}'
    '')

    # The Email Body

    email_body = ''

    for graph in graphs:
        _ = template
        _ = _.format(graph_url=graph, caption='')
        email_body += _

    # The Header of the Email

    Header = '<header> ' \
             '<h1 align="center">Zendesk Knowledge Base Analytics for the month of "{}" </h1>' \
             '<p align="center">(Click on the graphical image for more interactive graph)</p>' \
             '</header>'.format(v_LastMonth.strftime('%b %Y'))

    # Combine Header and Email Body to a single message.

    email_message = Header + email_body
    display(HTML(email_message))

    logger.debug("Email Content: '{}'".format(email_message))

    # Sender and receiver email address

    me = "Zendesk-KB-Analytics@noreply.pivotal.io"
    # If you want to add multiple receipents then add them like this
    # you = ["abc@xyz.com", "xyz@abc.com"]
    you = ["abc@xyz.com"]

    # Create message container - the correct MIME type is multipart/alternative.

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Zendesk Knowledge Base Analytics for Last Month"
    msg['From'] = me
    msg['To'] = ", ".join(you)

    # Create the body of the message (HTML version).

    part2 = MIMEText(email_message.encode('ascii', 'ignore'), 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.

    msg.attach(part2)

    # Send the message via local SMTP server.

    smtplib.SMTP()
    server = smtplib.SMTP('localhost.localdomain')
    logger.debug("SMTP server: '{}'".format(server))

    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.

    logger.info("Sending email to: '{0}' from: '{1}'".format(you,me))
    server.sendmail(me, you, msg.as_string())
    server.quit

    # End program message

    logger.info("End of the program: '{}'".format(__file__))

# Step 7
# Call the main function and start the program

main()

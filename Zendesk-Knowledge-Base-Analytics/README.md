# Overview

The "zendesk-knowledge-Base-Analytics.py" is a simple python script that gets the Zendesk API and plot graphs based on the data.

The graphs include

+ Total Articles contributed per months for last 12 months
+ The category that had the contribution last month
+ The contributors of last month
+ The Articles that are on draft mode
+ The Articles that are under KB reviewers queue
+ The Overall articles per category
+ The Overall TOP 10 articles contributors

# Requirement

+ Python 2.7.
+ smtp conigured on your local server ( check youtube on how to install postfix )
+ An account on plot.ly webiste , since the graphs are plotted based on their API calls
+ Import the necessary modules at are of Plotly
+ Set up credential locally after downloading the modules as indicated on the link https://plot.ly/python/getting-started/
+ If your server is having python 2.6 , the script wont work , since the plot.ly module fails with too many syntax errors.
+ Setup a virtual enviornment for python 2.7 ( refer to the blog post http://toomuchdata.com/2014/02/16/how-to-install-python-on-centos/ ) for step by step instruction on  how to install python 2.7
+ connection to the internet from the server
+ Install all the modules necessary for the program etc using "pip install" eg.s

# How to run

Run the program via

```
python <filename>
```
To enter into debug level run via

```
python <filename> -d 
```

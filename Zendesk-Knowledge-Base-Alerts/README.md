# Overview

The "new_KB_alerts.py" is a simple python script that gets the Zendesk API and detects when articles are published or updated and send alerts to necessary group.

# Requirement 

+ Python 2.7. 
+ smtp conigured on your local server ( check youtube on how to install postfix )
+ If your server is having python 2.6 then on the notepad find and replace the word '{}'  with  '{0}' (yes the single quotes is needed when searching and replacing )
+ connection to the internet from the server
+ Install all the modules (below) necessary for the program etc using "pip install" eg.s

```
pip install requests
pip install json
pip install python-dateutil
pip install jinja2
```

# How to run

Run the program via

```
python <filename>
```

To enter into debug level run via

```
python <filename> -d 
```

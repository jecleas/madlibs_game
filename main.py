import numpy as np
from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import urljoin

class wordlib():
    
    def __init__(self):
        self.name = "hello"
    pass

bats = wordlib()
print(bats.name)

## here are all the requirements I need to source the website

base_url = r'https://www.madtakes.com/index.php'
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'dnt': '1',
    'priority': 'u=0, i',
    'referer': 'https://www.madtakes.com/',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}

params = {
    'page': '-1',
}

response = requests.get(base_url, params=params, headers=headers)

madtakes_main = response

#If error and navigate

if madtakes_main.status_code != 200:
    print(f"Error Fetching Page - Error {madtakes_main.status_code}")
    exit()
else:
    mt_main_content = madtakes_main.content

mt_main_soup = BeautifulSoup(mt_main_content, 'html.parser')

soup = mt_main_soup

links = soup.find_all('a')

##put the new links in a dictionary with the link and name of the thing and show the user 

madLibs = {}
pattern_name = r">([^<]+)<"
pattern_link = r'href="([^"]*)"'

#using iteration I found that the links start at 22
for link in links[22:]:
    strLink = str(link)    
    if "Printable" in strLink or 'mG_none' in strLink:
        continue
    elif "Free" not in strLink:
        continue

    matchName = re.findall(pattern_name, strLink)[0]
    matchLink = re.findall(pattern_link, strLink)[0]

    ## I NEED A CONDITION HERE WHICH DOESN'T WRITE TO THE DICTIONARY IF THERE ARE EMPTIES - this needs to be added
    ##
    madLibs[matchName] = urljoin(base_url,matchLink)

## let the user navigate through the CLI on which one they would like to choose



## Once selected - use another func to navigate to that page

## Give the user options on what they should input in the CLI

##Print the end result when its completed

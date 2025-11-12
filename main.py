import numpy as np
from bs4 import BeautifulSoup
import requests
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

# Target the section that actually contains the story links instead of scanning
# every anchor on the page. The story list currently lives inside a card body
# (`mdl-card__supporting-text`). Falling back to the whole document keeps the
# scraper resilient if the page layout changes in the future.
story_container = soup.select_one(
    "div#storyList, div#stories_list, div.mdl-card__supporting-text"
)
if story_container is None:
    story_container = soup

##put the new links in a dictionary with the link and name of the thing and show the user

madLibs = {}


def is_story_link(anchor):
    """Return True when an anchor represents a playable Mad Lib story."""

    href = (anchor.get("href") or "").strip()
    if not href:
        return False

    text = anchor.get_text(strip=True)
    if not text:
        return False

    classes = " ".join(anchor.get("class", []))
    href_lower = href.lower()

    # Skip printable versions of the stories.
    if "print" in href_lower or "print" in classes:
        return False

    # Mad Takes story links consistently contain one of these keywords in the
    # href or the class list.
    keyword_matches_href = any(
        keyword in href_lower for keyword in ("/story/", "madlib", "libs/")
    )
    keyword_matches_class = any(
        "story" in class_name.lower() for class_name in anchor.get("class", [])
    )

    return keyword_matches_href or keyword_matches_class


for link in story_container.select("a[href]"):
    if not is_story_link(link):
        continue

    matchName = link.get_text(strip=True)
    matchLink = link.get("href", "")

    if not matchName or not matchLink:
        continue

    madLibs[matchName] = urljoin(base_url, matchLink)

## let the user navigate through the CLI on which one they would like to choose



## Once selected - use another func to navigate to that page

## Give the user options on what they should input in the CLI

##Print the end result when its completed

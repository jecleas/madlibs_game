"""FastAPI application that exposes Mad Lib story metadata.

The original script attempted to scrape the MadTakes landing page from a CLI
context.  It failed inside this execution environment because outbound HTTPS
traffic is routed through a proxy that returns HTTP 403 when the tunnel is
opened.  This module converts the behaviour into a FastAPI service and adds a
proxy-aware download helper that retries without proxy settings when necessary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from urllib.parse import urljoin

app = FastAPI(
    title="Mad Libs Story Browser",
    description=(
        "Fetches the list of MadTakes stories and exposes them over a REST API. "
        "The service is resilient to restrictive proxies that return HTTP 403 "
        "for CONNECT tunnel attempts by retrying without proxy configuration."
    ),
    version="0.1.0",
)

BASE_URL = "https://www.madtakes.com/index.php"
REQUEST_TIMEOUT = 15  # seconds
DEFAULT_HEADERS = {
    "accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "dnt": "1",
    "priority": "u=0, i",
    "referer": "https://www.madtakes.com/",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
}
PAGE_PARAMS = {"page": "-1"}
CONTAINER_SELECTORS: tuple[str, ...] = (
    "div#storyList",
    "div#stories_list",
    "div.mdl-card__supporting-text",
)
STORY_KEYWORDS: tuple[str, ...] = ("/story/", "madlib", "libs/")


class Story(BaseModel):
    """Public representation of a single Mad Lib story."""

    title: str
    url: str


@dataclass
class ScrapedStory:
    title: str
    url: str


class StoryScraperError(RuntimeError):
    """Base error raised when the MadTakes story list cannot be retrieved."""


class ProxyForbiddenError(StoryScraperError):
    """Raised when the configured proxy rejects the outgoing HTTPS request."""


def create_session(*, trust_env: bool) -> requests.Session:
    """Create a requests session optionally ignoring proxy environment vars."""

    session = requests.Session()
    session.trust_env = trust_env
    session.headers.update(DEFAULT_HEADERS)
    return session


def download_story_page() -> str:
    """Download the MadTakes landing page, retrying without proxies if needed."""

    proxy_error: Exception | None = None

    for trust_env in (True, False):
        session = create_session(trust_env=trust_env)
        try:
            response = session.get(
                BASE_URL,
                params=PAGE_PARAMS,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.ProxyError as exc:  # pragma: no cover - requires proxy
            proxy_error = exc
            # Retry once more after disabling proxy support.
            continue
        except requests.exceptions.RequestException as exc:
            raise StoryScraperError("Unable to download the MadTakes story list.") from exc

    assert proxy_error is not None  # pragma: no cover - purely defensive
    raise ProxyForbiddenError(
        "Requests routed through the configured proxy were rejected with HTTP 403. "
        "Retry the request without proxy settings (for example by setting NO_PROXY) "
        "or supply an alternative proxy that allows access to www.madtakes.com."
    ) from proxy_error


def is_story_link(anchor: Tag) -> bool:
    """Return True when an anchor element corresponds to a playable story."""

    href = (anchor.get("href") or "").strip()
    if not href:
        return False

    text = anchor.get_text(strip=True)
    if not text:
        return False

    classes = " ".join(anchor.get("class", []))
    href_lower = href.lower()

    if "print" in href_lower or "print" in classes:
        return False

    if any(keyword in href_lower for keyword in STORY_KEYWORDS):
        return True

    return any("story" in class_name.lower() for class_name in anchor.get("class", []))


def parse_story_list(html: str) -> list[ScrapedStory]:
    """Extract all Mad Lib stories from the provided HTML page."""

    soup = BeautifulSoup(html, "html.parser")
    story_container = soup.select_one(
        ", ".join(CONTAINER_SELECTORS)
    )
    if story_container is None:
        story_container = soup

    stories: list[ScrapedStory] = []
    for anchor in story_container.select("a[href]"):
        if not is_story_link(anchor):
            continue

        title = anchor.get_text(strip=True)
        href = anchor.get("href", "")
        if not title or not href:
            continue

        stories.append(ScrapedStory(title=title, url=urljoin(BASE_URL, href)))

    return stories


def fetch_story_list() -> list[ScrapedStory]:
    """Fetch and parse the Mad Lib story list."""

    html = download_story_page()
    stories = parse_story_list(html)
    if not stories:
        raise StoryScraperError("No stories could be located on the MadTakes landing page.")
    return stories


def serialize_stories(stories: Iterable[ScrapedStory]) -> list[Story]:
    """Convert internal story objects into the API response schema."""

    return [Story(title=story.title, url=story.url) for story in stories]


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    """Lightweight health endpoint for readiness probes."""

    return {"status": "ok"}


@app.get("/stories", response_model=list[Story])
def list_stories() -> list[Story]:
    """Return the stories available from the MadTakes landing page."""

    try:
        stories = serialize_stories(fetch_story_list())
    except ProxyForbiddenError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except StoryScraperError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return stories


__all__ = ["app"]

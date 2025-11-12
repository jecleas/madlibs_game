# Mad Libs Game API

This project exposes the MadTakes catalogue through a lightweight FastAPI
service.  The original CLI script has been replaced with a REST API that fetches
and parses the story list from <https://www.madtakes.com/index.php> using
`requests` and `BeautifulSoup`.

## Running locally

1. Create a virtual environment and install the dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the FastAPI application with Uvicorn:
   ```bash
   uvicorn main:app --reload
   ```
3. Open <http://127.0.0.1:8000/docs> to interact with the automatically
   generated API documentation.

## Proxy aware scraping

The environment used for development routes HTTPS requests through a corporate
proxy that rejects CONNECT tunnel attempts with HTTP 403.  The downloader inside
`main.py` first tries the request using the environment's proxy configuration
and, if that fails with a proxy error, retries with proxy handling disabled.  If
both attempts fail you will receive a `502` response from the API describing the
issue.

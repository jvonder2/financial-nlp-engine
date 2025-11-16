import os # Used to read environment variables (variables not stored in your code, but instead stored in the environment that your code runs, like a secret not that your computer can look up whenever they need important information) (like the API key)
import requests # Library for making HTTP requests to the FRED API  # pyright: ignore[reportMissingModuleSource]

FRED_BASE_URL = "https://api.stlouisfed.org/fred" # Base URL for all FRED API endpoints. We append specific endpoints (like /series/search) to this base


def _get_api_key() -> str: 
    """
    Internal helper function to get the FRED API key from an environment variable. Returns the key if found; raises an error if not found
    """
    api_key = os.getenv("FRED_API_KEY") # tries to read your computer's environment varibale named FRED_API_KEY. If it exists, it returns the string value and if it doesn't, it returns None
    if not api_key:  # If the API key could not be found, we STOP the program with a clear message. This prevents confusing errors later when trying to call the FRED API without a key.
        raise RuntimeError("FRED_API_KEY environment variable not set.")
    return api_key # If everything is OK, return the valid API key


def search_series(search_text: str, limit: int = 10) -> list[dict]:
    """
    Search for FRED data series whose tites or descriptions match a given search term. Returns a list of series metadata dictionaries
    """
    api_key = _get_api_key() # Get the API key so we can authenticate with the FRED API
    url = f"{FRED_BASE_URL}/series/search" # Construct the full URL for the FRED series search endpoint. This endpoint returns a list of series matching a keyword search
    params = { # Build the query parameters (the parts after the ? in a URL)
        "search_text": search_text, # What the user is searching for, (e.g: "inflation")
        "api_key": api_key, # Required API key
        "file_type": "json", # Ask FRED to return JSON (easier for Python to read)
        "limit": limit, # Maximum number of results FRED should return
    }
    resp = requests.get(url, params=params) # Make an HTTP GET request to the FRED API with the URL and parameters
    resp.raise_for_status() # Raises an error if the request was unsuccessful (anything not 200 OK). This avoids silent failures and helps debugging
    data = resp.json() # Convert the JSON response body into a Python dictionary
    return data.get("seriess", []) # The FRED API returns search results inside a "seriess" list. We extract it safely using .get() so the program doesn't crash if the key is missing
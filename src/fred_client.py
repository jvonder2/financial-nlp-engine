import os # Standard library module for interacting with the operating system (env vars, paths, etc.)
import requests # Third-party library used to make HTTP requests to web APIs (like FRED)  # pyright: ignore[reportMissingModuleSource]
from pathlib import Path # Path class for working with filesystem paths in a clean, object-oriented way

FRED_BASE_URL = "https://api.stlouisfed.org/fred" # Base URL for all FRED API endpoints which we will use as a base to build off of to make specific URLs

def _get_api_key() -> str:
    """
    Internal helper function to fetch the FRED API key from the environment variable FRED_API_KEY
    """
    api_key = os.getenv("FRED_API_KEY") # Read the environment variable names "FRED_API_KEY" and returns the value if there is one, returns none if not
    if not api_key:
        raise RuntimeError("FRED_API_KEY environment variable not set.") # Shows we can't call the FRED API properly, so it prints an error
    return api_key # If the key does exist, return it


def get_series_info(series_id: str) -> dict: 
    """
    Fetch metadata (descriptive info) about a FRED series,
    such as its title, frequency, units, etc.
    """
    api_key = _get_api_key() # Gets the API key from the environment
    url = f"{FRED_BASE_URL}/series" # Constructs the URL for the FRED "series" endpoint which returns metadata about a single time series
    params = { # Build initial query paramenters for the request
        "series_id": series_id, # Which series to download
        "api_key": api_key, # API key for authorization
        "file_type": "json", # We ask FRED for JSON so we can parse it in Python
    }
    resp = requests.get(url, params=params) # Send an HTTP GET request to the FRED API using the URL and parameters
    resp.raise_for_status() # If the HTTP status code indicates an error such as 4xx or 5xx, this will raise an exception instead of silently failing
    data = resp.json() # Parses the JSON file body into Python dictionaries
    # FRED wraps in 'seriess' list
    if "seriess" in data and data["seriess"]: # FRED wraps the series info under the key "seriess," so we check if that key exists
        return data["seriess"][0] # returns the first (and usually only) element of the seriess list being the dictionary that conatains the metadata
    return {} # If "seriess" is missing or empty, return an empty dictionary to signal "no data"
    

def download_series( 
    series_id: str, # The FRED series ID we want to download (ex: "UNRATE")
    start_date: str | None, # Optional start date filter (ex: "2010-01-01"), or None
    end_date: str | None, # Optional end date filter (ex: "2010-12-31"), or None
    frequency: str | None, # Optional frequency filter (ex: "m" for monthly), or None
    output_dir: str, # Folder where the download data file will be saved
    fmt: str = "csv", # Output file format: "csv" (default) or "json"
    max_rows: int | None = None, # Optional limit on how many observations to return; if None, FRED returns all available data
) -> str:
    """
    Download a FRED series and save to disk.
    Returns the path to the saved file as a string.
    fmt: 'csv' or 'json'
    """
    api_key = _get_api_key() # Get the API key from the environment so we can authenticate with FRED
    url = f"{FRED_BASE_URL}/series/observations" # Construct the URL for the FRED "series/observations" endpoint, which returns the actual time-series data points
    params = { # Build initial query parameters (minimum required parameters needed to make a valid request before adding any filters or optional settings) for the request
        "series_id": series_id, # Which series to download
        "api_key": api_key, # API key for authorization
        "file_type": "json", # We ask FRED for JSON so we can parse it in Python
    }
    if start_date: # If a start date was provided (not None or empty), add it to the parameters, telling FRED not to return data before this date
        params["observation_start"] = start_date
    if end_date: # If a end date was provided (not None or empty), add it to the parameters, telling FRED not to return data after this date
        params["observation_end"] = end_date
    if frequency: # If a frequency was provided (not None or empty), add it to the parameters. FRED can transform data to another frequency like monthly or quarterly
        params["frequency"] = frequency
    if max_rows: # If the user provided --max-rows, include a 'limit' parameter so FRED returns only that many observations
            params["limit"] = max_rows # Tells the FRED API the maximum number of data rows to send back

    resp = requests.get(url, params=params) # Make the HTTP GET request to FRED with our URL and parameters
    resp.raise_for_status() # If the HTTP status code indicates an error such as 4xx or 5xx, this will raise an exception instead of silently failing
    data = resp.json() # Parses the JSON file body into Python dictionaries

    output_dir_path = Path(output_dir) # Converts the output_dir string into a Path object for nicer path handling
    output_dir_path.mkdir(parents=True, exist_ok=True) # Ensures that the output directory exists. (parents=True means create any missing parent directories as well) (exist_ok=True means don't error if the directory already exists) (Uses mkdir rather than os.makedir because we turned it into a path object which words better for mkdir as os.makedir works with strings)

    if fmt == "json": # If the user asks for JSON format...
        output_path = output_dir_path / f"{series_id}.json" # Build the full path for the JSON output file (e.g: "data/raw/fred/UNRATE.json")
        output_path.write_text(resp.text, encoding="utf-8") # Write the raw response text (already in JSON format) to the file. We explicitly set encoding to "utf-8" to avoid encoding issues.
        return str(output_path) # Return the path to the file as a string

    # Default: CSV
    observations = data.get("observations", []) # Extract the list of observations (data points) from the JSON. (If 'observations' isn't present, default to an empty list)
    # Manually build CSV
    lines = ["date,value"] # We'll build a list of lines to form the CSV file content. Start with the header rown naming the columns
    for obs in observations: # Loop through each observation/data point in the list
        date = obs.get("date", "") # Get the date of this observation. If missing, fall back to empty string
        value = obs.get("value", "") # Get the numeric value (as string) for this observation. If missing, empty string
        lines.append(f"{date},{value}") # Append a CSV-formatted line like "2020-01-01,3.5" to our lines list
    csv_str = "\n".join(lines) # Join all lines together with the newline character to create the full CSV content

    output_path = output_dir_path / f"{series_id}.csv" # Build the full path for the CSV output file (e.g: data/raw/fred/UNRATE.csv")
    output_path.write_text(csv_str, encoding="utf-8") # Write the CSV string to the file, again using UTF-8 encoding (essentially prints these now joined lines list into the output file) (Uses utf-8 because that is the encoding that Mac/Linux machines use and is required by many APIs and is used by JSON inherently)
    return str(output_path) # Return the path to the saved CSV file as a string.
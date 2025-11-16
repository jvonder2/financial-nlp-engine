#!/usr/bin/env python3
"""
Command line tool for downloading FRED (Federal Reserve Economic Data) series
"""

import argparse
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')) # Tells python to look intside of the src directory for the ingestion module and other imports

from src.fred_client import download_series, get_series_info #
from src.fred_lookup import search_series

def main():
    # Creates an argument parser for handiling command line inputs (RawDescriptionHelpFormatter keeps formatting intact inside epilog)
    parser = argparse.ArgumentParser(description='Download FRED time series dtat', formatter_class=argparse.RawDescriptionHelpFormatter, epilog="""
    Examples:
  # Search for series
  python fetch_fred.py --search "unemployment rate"
  
  # Download a series by ID
  python fetch_fred.py --series-id UNRATE --start-date 2010-01-01 --end-date 2020-12-31
  
  # Download a series with custom output directory and format
  python fetch_fred.py --series-id GDP --output-dir ./data/raw/fred --format csv
        """
    ) # Adds a block of help text that appears when user runs: python fetch_fred.py -h


    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=False) # Creates a group where only one of the arguments can be used at a time (meaning you cannot pass --search and --series-id at the same time)
    input_group.add_argument('--search', help='Search for FRED series by name/description') # Defines the input option of --search which is a search for a FRED series by name/description (e.g: --search "inflation")


    # Filters / options
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)', default=None) # Creates an optional date filter for the start of the data range
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)', default=None) # Creates an optional date filter for the end of the data range
    parser.add_argument('--frequency', help='Observation frequency (e.g., m, q, a)', default=None) # Creates an optional frequency filter for the data (e.g: m = monthly, q = quarterly, a = annual)
    parser.add_argument('--output-dir', default='data/raw/fred',
                        help='Output directory for downloaded series (default: data/raw/fred)') # Where files are saved (Default: data/raw/fred)
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                        help='Output format for downloaded data (default: csv)') # Allows for the file to be formatted as a csv or a json file with it being a csv file by default
    parser.add_argument('--series-id', help='FRED series ID to download (e.g., GDP, UNRATE, FEDFUNDS)') # Defines the --series-id argument, which lets the user request a specific FRED series to download
    parser.add_argument('--max-rows', type=int, default=None, help='Maximum number of observations to download' # Optional argument that limits how many data points FRED should return (None means return all observations)
    )

    args = parser.parse_args() # Function that actually parses the arguments and returns them as an object (Stores all values (series-id, search, etc) in the args object)

    # Handle search mode
    if args.search: #only run this block if the user provided --search
        print(f"Searching FRED for series matching '{args.search}'...") # Prints a message to the console indicating that the search is beginning
        series_list = search_series(args.search, limit=10) # Calls the search_series function from the fred_lookup module and searches FRED for text query. Limits to the first 10 results

        if not series_list: # If there are no results, exit the function
            print("No series found.")
            return

        print(f"\nFound {len(series_list)} series:") # Prints a message to the console indicating that the search found results
        print("-" * 80) # Creates a separator line to make the output more readable(contains 80 hyphens)
        for i, s in enumerate(series_list, 1): #Loops through all returned results and nicely prints their IDs, titles, frequency, and units
            print(f"{i:2}. {s.get('id', 'Unknown')}: {s.get('title', 'No title')}")
            print(f"    Frequency: {s.get('frequency', 'Unknown')}")
            print(f"    Units: {s.get('units', 'Unknown')}")
            print() # s.get(..) prevents KeyError within the dictionaries used by returning certain responses if those keys are not available
        
        print("Use --series-id with one of the above IDs to download data.") # Tells the user the next step to do in order to download the data and exits the search module
        return

    # Validate that series-id was provided if not searching
    if not args.series_id: # If the user did NOT pass --search and did NOT pass --series-id, shows both a printed error and a help menu
        print("Error: Please provide --series-id or --search")
        parser.print_help() # print_help is a built-in method of the ArgumentParser from argparse that prints the formatted help menu above
        return

    series_id = args.series_id.upper() # Converts ID to uppercase (FRED series IDs are uppercase by convention)

    # Look up metadata (optional but nice)
    try: 
        info = get_series_info(series_id) # Helps user get metadata (such as ID, start date, end date, frequency, etc)
        series_title = info.get('title', series_id) # If available, grabs the human-readable title
    except Exception as e: # If the user typed an invalid series ID or something else occurred that caused the metadata request to fail, it will print a warning, attempt to download the actual data of the series anyway, and if the title is unable to be gotten, set it equal to the series ID
        print(f"Warning: could not fetch series info for {series_id}: {e}")
        series_title = series_id

    print(f"Downloading FRED series {series_id} - {series_title}...") # Friendly output showing series ID and reable name
    os.makedirs(args.output_dir, exist_ok=True) # Creates a directory if it is missing and doesn't return an error if it already exists

    try:
        output_path = download_series( # download_series is defined in fred_client.py and is responsible for contacting the FRED API, downloading the dataset, saving the file as a CSV or JSON file, and returning the path where it was saved
            series_id=series_id,
            start_date=args.start_date,
            end_date=args.end_date,
            frequency=args.frequency,
            output_dir=args.output_dir,
            fmt=args.format,
            max_rows=args.max_rows
        )

        print(f"\nCompleted! Saved data to {output_path}") # Confirms success to the user
    except Exception as e: # If anything goes wrong in the download process, print an error and exit with status code 1 in order to indicate the failure
        print(f"Error during FRED download: {e}")
        sys.exit(1)


if __name__ == "__main__": # Ensures that main only runs when the file is ran directly and not when the file is imported as a module
    main()
    
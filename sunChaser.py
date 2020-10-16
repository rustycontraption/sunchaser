import json
import requests
import argparse
from requests.exceptions import HTTPError

def main(location,days,distance):
    print ("")
    # pull data from noaa api
    # 

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="sun chaser",
        description="Find the nearest sun.")
    parser.add_argument(
        "--location",
        help="The starting location for trip.",
        action="store",
        default="seattle") # TODO: determine format of location data
    parser.add_argument(
        "--days",
        help="Maximum number of days for trip.",
        action="store",
        default=2)
    parser.add_argument(
        "--distance",
        help="Maximum distance in miles to search for sun.",
        action="store",
        default=100)

    args = parser.parse_args()

    main(args.location, args.days, args.distance)


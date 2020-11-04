import json
import requests
import datetime
import argparse
import pprint
import shapely.geometry
import pyproj
import geopy
import time
from datetime import datetime
from geopy.distance import geodesic
from requests.exceptions import HTTPError

def overpass_query(origin,distance):
    # Query Open Street Map for cities within 100,000 meters of Seattle
    # Return list of city names and lat/long coordinates
    # TODO: build query based on origin and distance
    result = requests.get("http://overpass-api.de/api/interpreter?data=[out:json];%28node%5B%22place%22%3D%22city%22%5D%28around%3A100000%2C47%2E6062%2C%2D122%2E3321%29%3Bnode%5B%22place%22%3D%22town%22%5D%28around%3A100000%2C47%2E6062%2C%2D122%2E3321%29%3B%29%3Bout%3B%0A")
    nodes = result.json()

    locations = {}
    for item in nodes["elements"]:
        locations[item["tags"]["name"]] = {
            "lat": item["lat"],
            "lon": item["lon"]
            }
    return locations
    
def utc2local (utc):
    # convert utc to local time
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
    return utc + offset

def query_noaa(locations):
    # Forecasts are divided into 2.5km grids. 
    # Each NWS office is responsible for a section of the grid.
    # get grid for each city in location, retrieve weather report for that grid,
    # then update location dictionary with relevant weather data

    for loc in locations:
        gridData = requests.get("https://api.weather.gov/points/" + str(locations[loc]["lat"]) + "," + str(locations[loc]["lon"])).json()
        weatherData = requests.get(gridData["properties"]["forecastGridData"]).json()
        locations[loc]["skyCover"] = weatherData["properties"]["skyCover"]
    
    return locations

def main(origin, distance):
    locations = overpass_query(origin, distance)
    query_noaa(locations)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="sun chaser",
        description="Find the nearest sun.")
    parser.add_argument(
        "--origin",
        help="The origining location for trip.",
        action="store",
        default="47.6062,-122.3321") # TODO: determine format of location data
    parser.add_argument(
        "--distance",
        help="Maximum distance in miles to search for sun.",
        action="store",
        default=200)

    args = parser.parse_args()

    main(args.origin, args.distance)

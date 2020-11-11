import json
import requests
import argparse
import pprint
import shapely.geometry
import pyproj
import geopy
import time
import dateutil
import os
from dateutil import parser
from datetime import datetime, timezone, timedelta
from geopy.distance import geodesic
from requests.exceptions import HTTPError

def query_overpass(origin,distance):
    print("querying overpass....")
    # Query Open Street Map for cities within given meters of origin
    # Return list of city names and lat/long coordinates

    result = requests.get(
        'http://overpass-api.de/api/interpreter?data=[out:json];\
            (node["place"="city"]\
                (around:' + distance + ',' + origin + ');\
            node["place"="town"]\
                (around:' + distance + ',' + origin + ');\
            );\
            out;'
        )
    nodes = result.json()

    data = {
        "timestamp": datetime.now(),
        "locations": {}
    }
    for item in nodes["elements"]:
        data["locations"][item["tags"]["name"]] = {
            "lat": item["lat"],
            "lon": item["lon"]
            }
    return data
    
def query_noaa(data):
    print("querying noaa...")
    # Forecasts are divided into 2.5km grids. 
    # Each NWS office is responsible for a section of the grid.
    # get grid for each city in location, retrieve weather report for that grid,
    # then update location dictionary with relevant weather data

    # Add timestamp for checking age of cached results
    data["timestamp"] = str(datetime.now())

    for loc in list(data["locations"]):
        print(loc)
        # Sleep between API requests to avoid hitting Google's request rate limit
        gridData = requests.get("https://api.weather.gov/points/" + 
            str(data["locations"][loc]["lat"]) + "," + 
            str(data["locations"][loc]["lon"])).json()
        time.sleep(.02)
        weatherData = requests.get(gridData["properties"]["forecastGridData"]).json()
        time.sleep(.02)

        # If a location doesn't have the required data, delete that location from the
        # dict.
        if "properties" in weatherData and "skyCover" in weatherData["properties"]:
            data["locations"][loc]["skyCover"] = weatherData["properties"]["skyCover"]
        else:
            del data["locations"][loc]
    
    print("done getting locations")

    # Cache results
    with open('locations.json', 'w') as outfile:
        json.dump(data, outfile)

    return data

def main(origin, distance):
    # Retrieve cities
    locations = query_overpass(origin, distance)

    # Retrieve weather forecast for cities.
    # First check if there is cached data we can use instead to
    # save ourselves the API requests.
    if os.path.exists("locations.json"):
        with open('locations.json') as data:
            locCache = json.load(data)
        if datetime.strptime(locCache['timestamp'], '%Y-%m-%d %H:%M:%S.%f') < datetime.now() + timedelta(hours = 1):
            locData = locCache
        else: locData = query_noaa(locations)
    else:
        locData = query_noaa(locations)

    # Obtaining forecast for desired the time is a pain in the ass.

    # Round our current time to nearest hour to compare with NOAAs
    # hourly forecasts
    currentTime = datetime.now(timezone.utc)
    roundedTime = currentTime.replace(second=0, microsecond=0, minute=0, hour=currentTime.hour) + timedelta(hours=currentTime.minute//30)
    for loc in locData["locations"]:
        for value in locData["locations"][loc]["skyCover"]["values"]:
            validTime = value["validTime"].split("/")[0]
            validTimeFormatted = dateutil.parser.parse(validTime)
            if validTimeFormatted == roundedTime:
                print(loc, value)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="sun chaser",
        description="Find the nearest sun.")
    parser.add_argument(
        "--origin",
        help="The origining location for trip in lat/lon coordinates.",
        action="store",
        default="47.6062,-122.3321")
    parser.add_argument(
        "--distance",
        help="Maximum distance in meters to search for sun.",
        action="store",
        default="10000")

    args = parser.parse_args()

    main(args.origin, args.distance)

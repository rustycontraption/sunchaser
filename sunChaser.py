import json
import requests
import argparse
import time
import os
import isodate
from dateutil import parser
from datetime import datetime, timezone, timedelta
from requests.exceptions import HTTPError


def query_overpass(origin, distance):
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

    locations = {
        "timestamp": datetime.now(),
        "locations": {}
    }

    for item in nodes["elements"]:
        locations["locations"][item["tags"]["name"]] = {
            "lat": item["lat"],
            "lon": item["lon"],
            "population": int(item["tags"].get("population", 0))
            }
    return locations


def query_noaa(data):
    print("querying noaa...")
    # Add timestamp for checking age of cached results
    data["timestamp"] = str(datetime.now())

    # Store NWS grids for each location so we can prune a
    # location if there is already a location in the same grid
    gridCheck = []

    for loc in list(data["locations"]):
        # Prune or retrieve forecast for locations.
        # Sleep between API requests to avoid hitting Google's request rate limit

        # Forecasts are divided into 2.5km grids. 
        # Each NWS office is responsible for a section of the grid.
        gridData = requests.get("https://api.weather.gov/points/" +
                                str(data["locations"][loc]["lat"]) + "," +
                                str(data["locations"][loc]["lon"])).json()
        data["locations"][loc]["grid"] = gridData["properties"]["forecastGridData"]

        # Prune location list to reduce further API calls
        if gridData["properties"]["forecastGridData"] in gridCheck:
            del data["locations"][loc]
            continue
        else:
            gridCheck.append(gridData["properties"]["forecastGridData"])

        # Retrieve weather data from NOAA
        try:
            response = requests.get(gridData["properties"]["forecastGridData"], timeout=2)
        except Exception as e:
            response = {}
            print(e)

        if (
            not response or
            response.status_code != 200
        ):
            print("del ", loc)
            del data["locations"][loc]
            continue
        else:
            print(response, loc)
            weatherData = response.json()

        # If a location doesn't have the required data, delete that location
        # from the dict.
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
        if datetime.strptime(locCache['timestamp'], '%Y-%m-%d %H:%M:%S.%f') > datetime.now() + timedelta(hours = -1):
            locData = locCache
        else: 
            locData = query_noaa(locations)
    else:
        locData = query_noaa(locations)

    # Obtaining forecast for desired the time is a pain in the ass.

    # Find current conditions
    # TODO: Add support for future forecasts
    currentTime = datetime.now(timezone.utc)
    for loc in locData["locations"]:
        for data in locData["locations"][loc]["skyCover"]["values"]:
            validTime = data["validTime"].split("/")
            forecastDuration = isodate.parse_duration(validTime[1])
            forecastTime = parser.parse(validTime[0])
            forecastEndTime = (forecastTime + forecastDuration) - timedelta(minutes=1)
            if currentTime >= forecastTime and currentTime <= forecastEndTime:
                print(loc, " sky cover is currently ", data["value"])


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
        default="15000")

    args = parser.parse_args()

    main(args.origin, args.distance)

import json
import requests
import argparse
import time
import os
import isodate
import click
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

    # Count results so we can report progress to user
    resultCount = 0

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
        # TODO: There must be a better way to handle timeouts
        try:
            response = requests.get(gridData["properties"]["forecastGridData"], timeout=1)
        except requests.exceptions.RequestException as err:
            response = {}
            print(err)

        if (
            not response or
            response.status_code != 200
        ):
            del data["locations"][loc]
            continue
        else:
            weatherData = response.json()

        # If a location doesn't have the required data, delete that location
        # from the dict.
        if "properties" in weatherData and "skyCover" in weatherData["properties"]:
            data["locations"][loc]["skyCover"] = weatherData["properties"]["skyCover"]
        else:
            del data["locations"][loc]
        
        resultCount += 1
        print("Retrieved this many results so far: ", resultCount)

    print("done getting locations")

    # Cache results
    with open('locations.json', 'w') as outfile:
        json.dump(data, outfile)

    return data


@click.command()
@click.option('--origin',
              help='The origining location for trip in lat/lon coordinates',
              default="47.6062, -122.3321",
              show_default=True)
@click.option('--distance',
              help="Maximum distance in meters to search for sun.",
              default="15000",
              show_default=True)
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

    # Find current conditions
    # TODO: Add support for future forecasts
    # TODO: Return data in easier to read format, table maybe?
    # TODO: Filter returned data to show only sunny places
    currentTime = datetime.now(timezone.utc)
    for loc in locData["locations"]:
        for data in locData["locations"][loc]["skyCover"]["values"]:
            # Obtaining forecast for desired the time is a pain in the ass.
            # TODO: We'll want to do this for other forecast data at some
            #       point, should split this out into helper function.
            validTime = data["validTime"].split("/")
            forecastDuration = isodate.parse_duration(validTime[1])
            forecastTime = parser.parse(validTime[0])
            forecastEndTime = (forecastTime + forecastDuration) - timedelta(minutes=1)
            if currentTime >= forecastTime and currentTime <= forecastEndTime:
                print(loc + " sky cover is currently " + str(data["value"]) + "%")


if __name__ == "__main__":

    main()

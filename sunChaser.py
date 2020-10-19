import json
import requests
import argparse
import pprint
from requests.exceptions import HTTPError

def find_locations(start, distance):
    # return a list of locations as we can use to query noaa for weather reports.
    # locations must be within given distance of given location, and in lat/long format.
    # locations = []

    # TODO: how?
    response = requests.get('http://api.geonames.org/findNearbyPlaceNameJSON?lat='+ str(start['lat']) + 
    '&lng=' + str(start['long']) + 
    '&cities=10000&radius=' + distance + 
    '&maxRows=10&localCountry=true&username=sunchaser')
    pp = pprint.PrettyPrinter(indent=4)
    print (pp.pprint(response.json()))
    # return locations

#def find_sun(locations, dates):
    # get weather reports for given date range at given locations.
    # return dictionary of locations and their weather
    
    # sunnyLoc = {}

    # for each loc in locations:
        # response = requests.get('NOAA_URL')
        # noaaData = response.json() 

        # if all days in noaaData are not rainy,
        #   sunnyLoc.append(loc:weather)
    
    #return sunnyLoc

def main(start, distance):
    start = {'lat':47.6062,'long':-122.3321}
    find_locations(start, distance)
    # sun = find_sun(find_locations(start, distance), dates)
    # if sun:
    #   print(list of sunny places)
    # else:
    #   print("no sun")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="sun chaser",
        description="Find the nearest sun.")
    parser.add_argument(
        "--start",
        help="The starting location for trip.",
        action="store",
        default="seattle") # TODO: determine format of location data
    parser.add_argument(
        "--distance",
        help="Maximum distance in miles to search for sun.",
        action="store",
        default="100")

    args = parser.parse_args()

    main(args.start, args.distance)

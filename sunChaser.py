import json
import requests
import argparse
import pprint
import shapely.geometry
import pyproj
import geopy
from geopy.distance import geodesic
from requests.exceptions import HTTPError

def generate_search_grid(origin,distance):
    # Construct a grid of lat/long coords centered on the origin

    # find bounding box coords based on origin
    swCoord = geodesic(kilometers=distance).destination(geopy.Point(origin), 200)
    neCoord = geodesic(kilometers=distance).destination(geopy.Point(origin), 42)

    # generate projection using bounding box coords
    projMt = pyproj.Proj('epsg:3857')
    projLl = pyproj.Proj('epsg:4326')
    pointSw = shapely.geometry.Point((swCoord.latitude,swCoord.longitude))
    pointNe = shapely.geometry.Point((neCoord.latitude,neCoord.longitude))
  
    stepsize = 80000 # grid spacing in meters

    # project bounding box to target projection
    projectedSw = pyproj.transform(projLl, projMt, pointSw.x, pointSw.y)
    projectedNe = pyproj.transform(projLl, projMt, pointNe.x, pointNe.y)

    # calculate grid of lat/long coords)
    gridpoints = []
    x = projectedSw[0]
    while x < projectedNe[0]:
        y = projectedSw[1]
        while y < projectedNe[1]:
            p = shapely.geometry.Point(pyproj.transform(projMt, projLl, x, y))
            gridpoints.append(p)
            y += stepsize
        x += stepsize

    return gridpoints

def find_locations(origin, distance):
    # return a list of locations we can use to query noaa for weather reports.
    # locations must be within given distance of given location, and in lat/long format.
    # 

    # generate grid of lat/long coords
    grid = generate_search_grid(origin,distance)
    
    locations = []

    # hey idiot, don't hardcode api keys
    googleApiKey = "AIzaSyABQeWj3QdTqBb9dWyBnu0kTlIP9QdBYpU"

    # look up the nearest town to each coordinate in the grid and store its
    # name and lat/long.
    for coord in grid:
        # query google for nearest town to each grid coord
        reverseGeoRes = requests.get("https://maps.googleapis.com/maps/api/geocode/json?" +
            "latlng=" + str(coord.x)+ "," + str(coord.y) +
            "&key=" + str(googleApiKey) +
            "&result_type=locality"
        )

        data = reverseGeoRes.json()
        
        if data['plus_code'].get('compound_code'):
            # store town name and lat/long 
    
            # some responses dont include the results field, so get town name from
            # the compound code instead.  If a response doesnt have a compound code
            # we ignore it.
            compoundCode = data['plus_code']['compound_code'].split(" ")[1:]
            town = " ".join(compoundCode)

            if data['results']:
                locations.append({
                    'town': town,
                    'lat': data['results'][0]['geometry']['location']['lat'],
                    'long': data['results'][0]['geometry']['location']['lng']
                })
            else:
                # some returned locations are missing results so we have to look up
                # lat/long ourselves
                address = '+'.join(compoundCode)
                geoRes = requests.get("https://maps.googleapis.com/maps/api/geocode/json?" +
                    "address=" + address + 
                    "&key=" + googleApiKey
                )
                geoData = geoRes.json()
                locations.append({
                    'town': town,
                    'lat': geoData['results'][0]['geometry']['location']['lat'],
                    'long': geoData['results'][0]['geometry']['location']['lng']
                })
                
    return locations

#def find_sun(locations, dates):
    # get weather reports for given date range at given locations.
    # return dictionary of locations and their weather
    
    # sunnyLoc = {}

    # for each loc in locations:
        # reverseGeoRes = requests.get('NOAA_URL')
        # noaaData = reverseGeoRes.json() 

        # if all days in noaaData are not rainy,
        #   sunnyLoc.append(loc:weather)
    
    #return sunnyLoc

def main(origin, distance):
    find_locations(origin, distance)
    # sun = find_sun(find_locations(origin, distance), dates)
    # if sun:
    #   print(list of sunny places)
    # else:
    #   print("no sun")

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

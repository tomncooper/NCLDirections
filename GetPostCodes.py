import csv

from Directions import reverse_geocode

api_key = "AIzaSyCK8ebIxG9SdI9fCzqsRmUpVeppokSQ5Xs"

with open("Data/test.csv") as csvfile:

    reader = csv.DictReader(csvfile)

    for row in reader:
        latlong = (row["Latitude"],row["Longitude"])

        print "Record: {}".format(row["Collision Reference "])
        print reverse_geocode(latlong, api_key)

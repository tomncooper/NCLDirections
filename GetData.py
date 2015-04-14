import ConfigParser

from Directions import *

#Get the settings from the config file
config = ConfigParser.SafeConfigParser()
config.read("Settings.cfg")

#Get the API key from the settings file
api_key = config.get('API', 'key')

#Get the input and output files from the settings file
input_filename = config.get('Files', 'input')
output_filename = config.get('Files', 'output')

#Set the depature time for transit directions
departure_time = get_departure_time("08:00:00")

#Get a list of dictionaries containing the start and destination postcodes
inputs = read_postcode_csv(input_filename)

#Get the total number of items for use in the console output
total = len(inputs)

#Open the output csv file for as long as it is needed
with open(output_filename, 'wb') as csvfile:

    #Set the header list
    fieldnames = ["UniqueID", "Origin Postcode", "Destination Postcode", "Driving Distance (m)", "Driving Duration (sec)","Bicycling Distance (m)", "Bicycling Duration (sec)", "Walking Distance (m)", "Walking Duration (sec)", "Transit Distance (m)", "Transit Duration (sec)", "Number of Transit Nodes", "Walking Distance to 1st stop (m)", "Walking Distance from last stop (m)", "Total Walking Distance (m)"]

    #Create the writer object
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, restval='NA')

    #Write the header containing the column names to the csv file
    writer.writeheader()

    #Get a directions dictionary for each set of postcodes and save them to the output csv
    for i, item in enumerate(inputs):
        print "Processing id: {} ({} of {})".format(item["UniqueID"], i+1, total)

        #Get the directions results from the api
        origin = item["OriginPostcode"]
        destination = item["DestinationPostcode"]

        #Check the post codes and if both are fine submit to the api if not insert "Not Valid"
        if check_postcode(origin) and check_postcode(destination):
            result = get_direction_data(item["UniqueID"], origin, destination, api_key, departure_time)
        elif check_postcode(origin) and not check_postcode(destination):
            result = {"UniqueID":item["UniqueID"], "Origin Postcode":item["Origin Postcode"], "Destination Postcode":"Not Valid"}
        elif not check_postcode(origin) and check_postcode(destination):
            result = {"UniqueID":item["UniqueID"], "Origin Postcode":"Not Valid", "Destination Postcode":item["Destination Postcode"]}
        else:
            result = {"UniqueID":item["UniqueID"], "Origin Postcode":"Not Valid", "Destination Postcode":"Not Valid"}

        #Write the dictionary to the csv file
        writer.writerow(result)

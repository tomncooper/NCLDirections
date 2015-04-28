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

#Set the depature time for transit directions using the time and weekday from teh settings file
departure_time = get_departure_time(config.get('Time', 'time'), config.getint('Time', 'day'))

#Get a list of dictionaries containing the start and destination postcodes from the input file
inputs = read_postcode_csv(input_filename)

#Get the total number of items for use in the console output
total = len(inputs)

#Open the output csv file for as long as it is needed
with open(output_filename, 'wb') as csvfile:

    #Set the header list
    fieldnames = ["UniqueID", "Origin Postcode", "Destination Postcode", "Driving Distance (m)","Driving Duration (sec)", "Driving request status", "Bicycling Distance (m)", "Bicycling Duration (sec)", "Bicycling request status", "Walking Distance (m)", "Walking Duration (sec)", "Walking request status", "Transit Request Status", "Transit Distance (m)", "Transit Duration (sec)", "Number of Transit Nodes", "Walking Distance to 1st stop (m)", "Walking Distance from last stop (m)", "Total Walking Distance (m)","Postcode Status","Transit Lines","Transit Departure Time"]

    #Create the writer object
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, restval='NA')

    #Write the header containing the column names to the csv file
    writer.writeheader()

    #Get a directions dictionary for each set of postcodes and save them to the output csv
    for i, item in enumerate(inputs):
        print "Processing id: {} ({} of {})".format(item["UniqueID"], i+1, total)

        #Write the dictionary to the csv file
        writer.writerow(get_directions(item, api_key, departure_time))

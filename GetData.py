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

#Set up the list to hold all the direction dictionaries
results = list()

#Get the total number of items for use in the console output
total = len(inputs)

#Get a directions dictionary for each set of postcodes and save them to the results 
for i, item in enumerate(inputs):
    print "Processing id: {} ({} of {})".format(item["UniqueID"], i+1, total) 
    results.append(get_direction_data(item["OriginPostcode"], item["DestinationPostcode"], api_key, departure_time))

#Save all the results to the CSV file
write_to_csv(output_filename, results)

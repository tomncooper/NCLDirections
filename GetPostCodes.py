import csv, ConfigParser

from Directions import reverse_geocode, check_postcode

#Get the settings from the config file
config = ConfigParser.SafeConfigParser()
config.read("Settings.cfg")

api_key = config.get('API', 'key')
inputfile = config.get('Files', 'latlong')
outputfile = config.get('Files', 'postcodes')

with open(inputfile, 'rb') as csvfile:
    with open(outputfile, 'wb') as outfile:

        reader = csv.DictReader(csvfile)
        writer = csv.writer(outfile)

        #Write the header row for the output file
        writer.writerow(["Reference", "Latitude", "Longitude", "Postcodes"])

        for row in reader:
            latlong = (row["Latitude"],row["Longitude"])

            print "Processing record: {}".format(row["Collision Reference "])
            results = reverse_geocode(latlong, api_key)

            if results:
                #Add the id and lat/long for reference
                valid_pc = [row["Collision Reference "], latlong[0], latlong[1]]

                #Cycle through the postcode results and reject any that are not full postcodes
                valid_found = False
                for result in results:
                    if check_postcode(result):
                        valid_pc.append(result)
                        valid_found = True

                #If at least one of the postcodes is valid save the results to the file
                if valid_found:
                    writer.writerow(valid_pc)
                else:
                    print "Only partial postcodes found"
            else:
                #If the results are empty post to the console
                print "No postcodes found"

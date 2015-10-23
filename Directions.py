import requests
import csv
import time
import pytz
import datetime
import re

def get_waypoint_string(waypoints):
    """ Creates a string of postcodes seperated by pipes (|) from the supplied list of postcodes

    Arguments:
        waypoints - Iterable - containing postcode strings

    Returns:
        String of postcodes seperated by pipes (|)
    """

    wps = ""

    for i, wp in enumerate(waypoints):
        if i == 0:
            wps = wps + wp
        else:
            wps = wps + "|" + wp

    return wps

def get_dist_duration(UniqueID, start, end, api_key, waypoints = None):
    """ Gets distance and duration of a journey between start and end postcodes for driving, cycling and walking.

    Arguements:
        UniqueID - String - The unique ID number for this postcode start-end pair
        start - String - Origin postcode
        end - String - Destination postcode
        api_key - String - The google_api key to be used for the request
        waypoints - Iterable - Containing a list of intermediate waypoint postcodes

    Returns:
        A dictionary containing the origin and destination postcodes and the distance and duration for each mode of transport
        Dictionary keys:
            "Origin Postcode",
            "Destination Postcode",
            "Driving Distance (m)",
            "Driving Duration (sec)",
            "Bicycling Distance (m)",
            "Bicycling Duration (sec)",
            "Walking Distance (m)",
            "Walking Duration (sec)"
    """
    #Array containing modes of transport for which information is requested - transit handled separately below as output is more complex
    modes = ('driving', 'bicycling', 'walking')

    #Set up a list containing the column header names for each of the distance and duration values to be added as keys to the values dictionary
    colnames = (("Driving Distance (m)","Driving Duration (sec)", "Driving request status"),("Bicycling Distance (m)", "Bicycling Duration (sec)", "Bicycling request status"),("Walking Distance (m)", "Walking Duration (sec)", "Walking request status"))

    #The dictionary that will store distance and duration for the start and end postcodes supplied for each travel mode
    values = dict()

    #Add the start and end post codes to the values dictionary
    values["UniqueID"] = UniqueID
    values["Origin Postcode"] = start
    values["Destination Postcode"] = end

    #Cycle through the transport modes and get the directions for each
    for i, mode in enumerate(modes):

        #Make the appropriate request, depending on weather waypoints are needed, to the Google Directions API
        if waypoints:
            r = requests.get('https://maps.googleapis.com/maps/api/directions/json?origin={}&destination={}&waypoints={}&mode={}&key={}'.format(start, end, get_waypoint_string(waypoints), mode, api_key))
        else:
            r = requests.get('https://maps.googleapis.com/maps/api/directions/json?origin={}&destination={}&mode={}&key={}'.format(start, end, mode, api_key))

        #If the request is not successful print an error and do no further processing for this record
        if r.status_code != 200:
            print "Request network error"
        else:
            #Turn the returned JSON string into a dictionary
            result = r.json()
            #Get the status string and print it to the console
            status = result.get('status')
            print colnames[i][2] + ": " + status

            #If the request went through ok then add the results to the values dictionary
            if status == "OK":
                #Get list of legs for this direction request
                legs = result.get('routes')[0].get('legs')

                #Initialise the counter variables for the total distance and duration
                distance = 0.0
                duration = 0.0

                #Cycle through each of the legs in this route
                for leg in legs:
                    #Adds distance of leg to values dictionary using value of distance from distance dictionary which is in the leg dictionary
                    distance = distance + leg.get('distance').get('value')
                    #Adds duration of leg to values dictionary using value of duration from duration dictionary which is in the leg dictionary
                    duration = duration + leg.get('duration').get('value')

                #Once we have cycled through all the legs of the route save the totals to the values dictionary
                values[colnames[i][0]] = distance
                values[colnames[i][1]] = duration

            #Add the status to the output
            values[colnames[i][2]] = status

        #Sleep for half a second to prevent overloading the API
        time.sleep(0.5)

    return values

def get_departure_time(departure_time, weekday = 2):
    """ Gets the number of seconds since the epoch (midnight 01/01/1970) to the next weekday (wednesday as default as this is unlikly to be a public holiday) at the provided time.

    Arguments:
        departure_time - String - Time of day in the format HH:mm:ss
        weekday - Integer - The day of the week to set the datetime object to. Monday = 0, Sunday = 6

    Returns:
        Integer - The number of seconds since the epoch (midnight 01/01/1970) to the next suplied weekday at the provided time
    """

    #Create a time zone information object
    bst = pytz.timezone('Europe/London')

    #Get a datetime object for now in the timezone defined above
    now = datetime.datetime.now(bst)

    #Calculate the number of days ahead of the required day of the week we are
    days_ahead = weekday - now.weekday()

    #If we have passed the required day of the week increase the days ahead to account for this
    if days_ahead <= 0 :
        days_ahead = days_ahead + 7
    next_weekday = now + datetime.timedelta(days=days_ahead)

    #Get the hours minutes and seconds from the depature time string
    departure_time = departure_time.split(":")
    hour = int(departure_time[0])
    minutes = int(departure_time[1])
    seconds = int(departure_time[2])

    #Get a datetime object for the next required weekday at the required time
    new_date = next_weekday.replace(hour=hour, minute=minutes, second=seconds)

    #Get a datetime object for the epoch
    epoch = datetime.datetime(year = 1970, month = 1, day = 1, minute = 0, second = 0, tzinfo = bst)

    #Get the difference between the new date and the epoch in seconds
    dt_secs = int((new_date - epoch).total_seconds())

    print "Depature Time:"
    print datetime.datetime.fromtimestamp(dt_secs)

    return dt_secs

def get_single_transit_journey(start, end, api_key, departure_time = None):
    """ Gets direction information (see dictionary keys) for public transport between the supplied start and end postcodes. This method assumes no intermediat waypoints and uses the 1st returned route.

    Arguements:
        start - String - Origin postcode
        end - String - Destination postcode
        api_key - String - The google_api key to be used for the request
        departure_time - Integer - The number of seconds since the epoch (midnight 01/01/1970) the default is the current time

    Returns:
        A dictionary containing the origin and destination postcodes and the distance and duration for each mode of transport
        Dictionary keys:
            "Transit Distance (m)",
            "Transit Duration (sec)",
            "Number of Transit Nodes",
            "Walking Distance to 1st stop (m)",
            "Walking Distance from last stop (m)",
            "Total Walking Distance (m)"
    """

    #The dictionary that will store the transit information for the supplied origin and destination
    values = dict()

    #Make the request to the Google Directions API
    if departure_time:
        #If a depature time is provided use it
        r = requests.get('https://maps.googleapis.com/maps/api/directions/json?origin={}&destination={}&mode=transit&depature_time={}&key={}'.format(start, end, departure_time, api_key))
    else:
        #If no depature time is provided use the current time (this is the default api behaviour if not time is provided)
        r = requests.get('https://maps.googleapis.com/maps/api/directions/json?origin={}&destination={}&mode=transit&key={}'.format(start, end, api_key))

    if r.status_code != 200:
        print "Request Error"
    else:
        #For every request there is an associated status - turn the returned JSON string into a dictionary
        result = r.json()
        #Get the status string and print it to the console
        status = result.get('status')
        print "Transit Status: " + status

        #Add the Transit status to the values dictionary
        values["Transit Request Status"] = status

        if status == "OK":
            #Get the 1st leg of the 1st route
            leg = result.get('routes')[0].get('legs')[0]
            #Add the total distance and duration to the values dictionary
            values["Transit Distance (m)"] = leg.get('distance').get('value')
            values["Transit Duration (sec)"] = leg.get('duration').get('value')

            #Get the steps for this transit direction - returns list of step objects
            steps = leg.get('steps')

            #Add the number of nodes in the transit directions by getting length of steps array
            nsteps = len(steps)
            values["Number of Transit Nodes"] = nsteps

            #Get the walking distance for the 1st and last nodes. Uses -1 because zero indexed. If the 1st and last steps are not walking then add 0 to indicate negligble walking
            if steps[0].get('travel_mode') == 'WALKING':
                values["Walking Distance to 1st stop (m)"] = steps[0].get('distance').get('value')
            else:
                values["Walking Distance to 1st stop (m)"] = 0.0

            if steps[nsteps-1].get('travel_mode') == 'WALKING':
                values["Walking Distance from last stop (m)"] = steps[nsteps-1].get('distance').get('value')
            else:
                values["Walking Distance from last stop (m)"] = 0.0

            #Calculate TOTAL walking distance involved in transit route. Start by setting the total walking distance to zero.
            walking_dist = 0.0

            #For each step that Google labels as "WALKING" add the distance to the prior total walking from above.
            print "Transit Lines:"
            lines = ""
            for step in steps:
                if step.get('travel_mode') == 'WALKING':
                    walking_dist = walking_dist + step.get('distance').get('value')
                else:
                    #Print out the name of the transit line to the console to help with verification
                    line_name = step.get("transit_details").get("line").get("short_name")
                    if line_name:
                        lines = lines + " " + line_name
                        print line_name
                    else:
                        print "Error: no transit line name found"


            #Add the total walking distance
            values["Total Walking Distance (m)"] = walking_dist

            #Add the list of tranist lines to the vaules dictionary
            values["Transit Lines"] = lines

            #Add the departure time used in the request
            values["Transit Departure Time"] = datetime.datetime.fromtimestamp(departure_time)

    #Sleep for half a second to prevent overloading the API
    time.sleep(0.5)

    return values

def create_waypoint_pairs(start, end, waypoints):
    """ Creates a list of postcode pairs starting with the supplied start and end postcode.

    Arguments:
        start - String - Origin postcode
        end - String - Destination postcode
        waypoints - Iterable - List of waypoint postcode strings

    Returns:
        A list of post code pairs
    """
    pairs = list()
    n = len(waypoints) - 1
    for i, wp in enumerate(waypoints):
        if i == 0:
            pairs.append((start, waypoints[i]))
        else:
            pairs.append((waypoints[i-1],waypoints[i]))

    pairs.append((waypoints[n],end))

    return pairs

def get_transit_details(start, end, api_key, departure_time = None, waypoints = None):
    """ Gets direction information (see dictionary keys) for public transport between the supplied start and end postcodes and will include intermediate waypoints if supplied.

    Arguements:
        start - String - Origin postcode
        end - String - Destination postcode
        api_key - String - The google_api key to be used for the request
        departure_time - Integer - The number of seconds since the epoch (midnight 01/01/1970) the default is the current time
        waypoints - Iterable - List of waypoint postcode strings

    Returns:
        A dictionary containing the origin and destination postcodes and the distance and duration for each mode of transport
        Dictionary keys:
            "Transit Distance (m)",
            "Transit Duration (sec)",
            "Number of Transit Nodes",
            "Walking Distance to 1st stop (m)",
            "Walking Distance from last stop (m)",
            "Total Walking Distance (m)"
    """
    if waypoints:

        print "Running Transit Waypoints:"

        #Get a list of waypoint pairs
        pairs = create_waypoint_pairs(start, end, waypoints)

        #Set up the total dictionary and initialise the key value pairs
        total = dict()
        total["Transit Distance (m)"] = 0.0
        total["Transit Duration (sec)"] = 0.0
        total["Number of Transit Nodes"] = 0
        total["Walking Distance to 1st stop (m)"] = 0.0
        total["Walking Distance from last stop (m)"] = 0.0
        total["Total Walking Distance (m)"] = 0.0
        total["Transit Request Status"] = "OK"
        total["Transit Lines"] = ""
        total["Transit Departure Time"] = datetime.datetime.fromtimestamp(departure_time)

        #Cycle through the waypoint pairs and add each value to the total
        for i, pair in enumerate(pairs):

            pair_details = get_single_transit_journey(pair[0], pair[1], api_key, departure_time)

            if pair_details["Transit Request Status"] != "OK":
                total["Transit Request Status"] = pair_details["Transit Request Status"]

            total["Transit Distance (m)"] = total["Transit Distance (m)"] + pair_details["Transit Distance (m)"]
            total["Transit Duration (sec)"] = total["Transit Duration (sec)"] + pair_details["Transit Duration (sec)"]
            total["Number of Transit Nodes"] = total["Number of Transit Nodes"] + pair_details["Number of Transit Nodes"]
            total["Walking Distance to 1st stop (m)"] =  total["Walking Distance to 1st stop (m)"] + pair_details["Walking Distance to 1st stop (m)"]
            total["Walking Distance from last stop (m)"] = total["Walking Distance from last stop (m)"] + pair_details["Walking Distance from last stop (m)"]
            total["Total Walking Distance (m)"] = total["Total Walking Distance (m)"] + pair_details["Total Walking Distance (m)"]
            total["Transit Lines"] = total["Transit Lines"] + " Waypoint {}: ".format(i+1) + pair_details["Transit Lines"]

        return total
    else:
        return get_single_transit_journey(start, end, api_key, departure_time)

def get_direction_data(UniqueID, start, end, api_key, depature_time = None, waypoints = None):
    """ Gets direction information (see dictionary keys) for various transport methods between the supplied start and end postcodes, with optional waypoints.

    Arguements:
        UniqueID - String - The unique ID number for this postcode start-end pair
        start - String - Origin postcode
        end - String - Destination postcode
        api_key - String - The google_api key to be used for the request
        departure_time - Integer - The number of seconds since the epoch (midnight 01/01/1970) the default is the current time
        waypoints - Iterable - Containing the intermediate waypoint postcodes

    Returns:
        A dictionary containing the origin and destination postcodes and the distance and duration for each mode of transport
        Dictionary keys:
            "Origin Postcode",
            "Destination Postcode",
            "Driving Distance (m)",
            "Driving Duration (sec)",
            "Bicycling Distance (m)",
            "Bicycling Duration (sec)",
            "Walking Distance (m)",
            "Walking Duration (sec)"
            "Transit Distance (m)",
            "Transit Duration (sec)",
            "Number of Transit Nodes",
            "Walking Distance to 1st stop (m)",
            "Walking Distance from last stop (m)",
            "Total Walking Distance (m)"
    """

    #Get the indervidual dictionaries for the different transport modes
    vals = get_dist_duration(UniqueID, start, end, api_key, waypoints)
    trans = get_transit_details(start, end, api_key, depature_time, waypoints)

    #Combine them into one dictionary
    data = vals.copy()
    data.update(trans)

    return data

def read_postcode_csv(filename):
    """ Reads a csv file and returns a list of dictionary objects with the column headers as keys.

    Arguments:
        filename - String - The filename of the csv file that is to be opened

    Returns:
        A list of dictionary objects, eack of which represents a row of the csv with the keys as the column names.
    """
    #Create the data list
    data = list()

    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            data.append(row)

    return data

def check_postcode(postcode):
    """ Checks if the supplied string matches the pattern for a UK post code. Note that this method does not actually check if a postcode actually exists. This method also expects a space in the middle of the postcode.

    Arguments:
        postcode - String - A string to be checked against the postcode pattern

    Returns:
        Boolean indicating if the supplied string contains a valid postcode pattern.
    """
    pattern = "^(?:(?:[A-PR-UWYZ][0-9]{1,2}|[A-PR-UWYZ][A-HK-Y][0-9]{1,2}|[A-PR-UWYZ][0-9][A-HJKSTUW]|[A-PR-UWYZ][A-HK-Y][0-9][ABEHMNPRV-Y])? [0-9][ABD-HJLNP-UW-Z]{2}|GIR 0AA)$"

    if re.match(pattern, postcode.upper()):
        return True
    else:
        return False

def get_waypoint_list(input_data, NA_char = "99"):
    """ Gets a list of valid postcode waypoints from the supplied input dictionary, ignoring any cell that uses the NA character.

    Arguments:
        input_data - Dictionary - Data read from the input csv
        NA_char - String - The character used to signal missing data in the input csv file

    Returns:
        A list of postcode strings taken from the input data
    """

    #Get the dictionary keys that contain the word Waypoint
    waypoint_keys = list()
    for key in input_data.keys():
        if "Waypoint" in key:
            waypoint_keys.append(key)

    #If there are waypoints in the input data then process them, else return none
    if waypoint_keys:
        #Search through the waypoints and record those which are not the NA character
        waypoints = list()
        for waypoint in waypoint_keys:
            wp = input_data.get(waypoint).strip()
            if wp != NA_char:
                waypoints.append(wp)

        #If there is 1 or more valid waypoint then return the list else return none
        if waypoints:
            return waypoints
        else:
            return None
    else:
        return None

def get_directions(input_data, api_key, departure_time):
    """ Checks all supplied postcodes and prevents a call to the api of any are invalid. Note that this method assumes a space in the middle of the postcode inorder to be valid.

    Arguments:
        input_data - Dictionary - read from the input data csv file
        api_key - String - The Google API to make the request with
        departure_time - Integer - The number of seconds since the epoch (midnight 01/01/1970) the default is the current time

    Returns:
        A dictionary containing the origin and destination postcodes and the distance and duration for each mode of transport
        Dictionary keys:
            "Origin Postcode",
            "Destination Postcode",
            "Driving Distance (m)",
            "Driving Duration (sec)",
            "Bicycling Distance (m)",
            "Bicycling Duration (sec)",
            "Walking Distance (m)",
            "Walking Duration (sec)"
            "Transit Distance (m)",
            "Transit Duration (sec)",
            "Number of Transit Nodes",
            "Walking Distance to 1st stop (m)",
            "Walking Distance from last stop (m)",
            "Total Walking Distance (m)"
    """
    #Get the origin and destinations postcodes and the list of waypoints, if any
    origin = input_data["OriginPostcode"].strip()
    destination = input_data["DestinationPostcode"].strip()
    waypoints = get_waypoint_list(input_data)

    #Check the post codes and if both are fine submit to the api if not insert "Not Valid" into the postcode status field
    check_origin = check_postcode(origin)
    check_destination = check_postcode(destination)

    check_waypoints = True
    if waypoints:
        for waypoint in waypoints:
            if not check_postcode(waypoint):
                check_waypoints = False

    if check_origin and check_destination and check_waypoints:
        result = get_direction_data(input_data["UniqueID"], origin, destination, api_key, departure_time, waypoints)
        result["Postcode Status"] = "OK"
    elif check_origin and check_waypoints and not check_destination:
        result = {"UniqueID":input_data["UniqueID"], "Origin Postcode":origin, "Destination Postcode":destination, "Postcode Status":"Invalid Destination Postcode: '{}'".format(destination)}
        print "Error: Invalid Destination Postcode: '{}'".format(destination)
    elif not check_origin and check_destination and check_waypoints:
        result = {"UniqueID":input_data["UniqueID"], "Origin Postcode":origin, "Destination Postcode":destination, "Postcode Status":"Invalid Origin Postcode: '{}'".format(origin)}
        print "Error: Invalid Origin Postcode: '{}'".format(origin)
    elif check_origin and check_destination and not check_waypoints:
        result = {"UniqueID":input_data["UniqueID"], "Origin Postcode":origin, "Destination Postcode":destination, "Postcode Status":"One or more waypoints invalid"}
        print "Error: One or more invalid waypoint postcodes"
    else:
        result = {"UniqueID":input_data["UniqueID"], "Origin Postcode":origin, "Destination Postcode":destination, "Postcode Status":"Destination and Origin Invalid"}
        print "Error: All postcodes are invalid"

    return result

def reverse_geocode(latlong, api_key):
    """ Accepts a (latitude, longitude) tuple and reverse geocodes it into Post Codes.

    Arguments:
        latlongs - Tuple - latitude and longitude coordinates to be converted to a PostCode
        api_key - String - The google_api key to be used for the request

    Returns:
        A list of Post Code Strings that relate to the supplied latitude and longitude
    """

    postcodes = list()

    latitude = latlong[0]
    longitude = latlong[1]

    #Make the request to the Google GeoCoding API
    r = requests.get("https://maps.googleapis.com/maps/api/geocode/json?latlng={},{}&result_type=postal_code&key={}".format(latitude,longitude,api_key))

    #If the request is not successful print an error and do no further processing for this record
    if r.status_code != 200:
        print "Request network error"
        postcodes.append("Request Error")
    else:
        #For every request there is an associated status - turn the returned JSON string into a dictionary and pull out the list of results
        results = r.json().get("results")

        #Cycle through the list of result json objects
        for result in results:

            #Cycle through the list of Address component objects
            for component in result.get("address_components"):

                #For each component pull out the list of types that describe this component
                for component_type in component.get("types"):

                    #If any of this component's types match the postal_code type then save the short_name value of this component to the post codes list
                    if component_type == "postal_code":
                        pc = component.get("short_name")

                        #Check if this a valid length post code
                        if check_postcode(pc):
                            postcodes.append(pc)


    return postcodes

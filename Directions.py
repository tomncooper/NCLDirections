import requests
import csv
import time
import datetime
import os.path

def get_dist_duration(UniqueID, start, end, api_key):
    """ Gets distance and duration of a journey between start and end postcodes for driving, cycling and walking.
    
    Arguements:
        UniqueID - String - The unique ID number for this postcode start-end pair
        start - String - Origin postcode
        end - String - Destination postcode
        api_key - String - The google_api key to be used for the request
        
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
    colnames = (("Driving Distance (m)","Driving Duration (sec)"),("Bicycling Distance (m)", "Bicycling Duration (sec)"),("Walking Distance (m)", "Walking Duration (sec)"))
    
    #The dictionary that will store distance and duration for the start and end postcodes supplied for each travel mode
    values = dict()

    #Add the start and end post codes to the values dictionary
    values["UniqueID"] = UniqueID
    values["Origin Postcode"] = start
    values["Destination Postcode"] = end

    #Cycle through the transport modes and get the directions for each
    for i, mode in enumerate(modes):
        
        #Make the request to the Google Directions API
        r = requests.get('https://maps.googleapis.com/maps/api/directions/json?origin={}&destination={}&mode={}&key={}'.format(start, end, mode, api_key))
        
        #If the request is not successful print an error
        if r.status_code != 200:
            print "Request error"
        else:
            #If request is successful, turn the returned JSON string into a dictionary and get first leg of first routes - this makes leg a dictionary
            leg = r.json().get('routes')[0].get('legs')[0]
            #Adds distance of leg to values dictionary using value of distance from distance dictionary which is in the leg dictionary
            values[colnames[i][0]] = leg.get('distance').get('value')
            #Adds duration of leg to values dictionary using value of duration from duration dictionary which is in the leg dictionary
            values[colnames[i][1]] = leg.get('duration').get('value')

        #Sleep for half a second to prevent overloading the API
        time.sleep(0.5)

    return values
    
def get_departure_time(departure_time, weekday = 2):
    """ Gets the number of seconds since the epoch (midnight 01/01/1970) to the next weekday (wednesday as default as this is unlikly to be a public holiday) at the provided time. 
    
    Arguments:
        departure_time - String - Time of day in the format HH:mm:ss
        weekday - Integer - The day of the week to set the datetime object to. Monday = 0, Sunday = 6 
        
    Returns:
        Integer - The number of seconds since the epoch (midnight 01/01/1970) to the next monday at the provided time
    """    
    #Get a datetime object for now
    now = datetime.datetime.now()
    
    #Calculate the number of days ahead of the required day of the week we are
    days_ahead = weekday - now.weekday()
    
    #If we have passed the required day of the week increase the days ahead to account for this
    if days_ahead <= 0 :
        days_ahead = days_ahead + 7
    
    #Get a datetime object for the next required weekday
    next_weekday = now + datetime.timedelta(days=days_ahead)
    
    #Get the hours minutes and seconds from the depature time string
    departure_time = departure_time.split(":")
    hour = int(departure_time[0])
    minutes = int(departure_time[1])
    seconds = int(departure_time[2])
    
    #Get a datetime object for the next required weekday at the required time
    new_date = next_weekday.replace(hour=hour, minute=minutes, second=seconds)
    
    #Get a datetime object for the epoch
    epoch = datetime.datetime(1970,1,1)
    
    #Get the difference between the new date and the epoch in seconds
    dt_secs = int((new_date - epoch).total_seconds())

    print "Depature Time:"
    print datetime.datetime.fromtimestamp(dt_secs)
    
    return dt_secs
    
def get_transit_details(start, end, api_key, departure_time = None):
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
        #Get the 1st leg of the 1st route
        leg = r.json().get('routes')[0].get('legs')[0]
        #Add the total distance and duration to the values dictionary
        values["Transit Distance (m)"] = leg.get('distance').get('value')
        values["Transit Duration (sec)"] = leg.get('duration').get('value')

        #Get the steps for this transit direction - returns list of step objects
        steps = leg.get('steps')

        #Add the number of nodes in the transit directions by getting length of steps array
        values["Number of Transit Nodes"] = len(steps)

        #Get the walking distance for the 1st and last nodes. Uses -1 because zero indexed. If the 1st and last steps are not walking then add 0 to indicate negligble walking
        if steps[0].get('travel_mode') == 'WALKING':
            values["Walking Distance to 1st stop (m)"] = steps[0].get('distance').get('value')
        else:
            values["Walking Distance to 1st stop (m)"] = 0.0
        
        if steps[len(steps)-1].get('travel_mode') == 'WALKING':
            values["Walking Distance from last stop (m)"] = steps[len(steps)-1].get('distance').get('value')
        else:
            values["Walking Distance from last stop (m)"] = 0.0

        #Calculate TOTAL walking distance involved in transit route. Start by setting the total walking distance to zero.
        walking_dist = 0.0
        
        #For each step that Google labels as "WALKING" add the distance to the prior total walking from above.
        for step in steps:
            if step.get('travel_mode') == 'WALKING':
                walking_dist = walking_dist + step.get('distance').get('value')

        #Add the total walking distance
        values["Total Walking Distance (m)"] = walking_dist

    #Sleep for half a second to prevent overloading the API
    time.sleep(0.5)

    return values

def get_direction_data(UniqueID, start, end, api_key, depature_time = None):
    """ Gets direction information (see dictionary keys) for various transport methods between the supplied start and end postcodes. This method assumes no intermediat waypoints and uses the 1st returned route. 
    
    Arguements:
        UniqueID - String - The unique ID number for this postcode start-end pair
        start - String - Origin postcode
        end - String - Destination postcode
        api_key - String - The google_api key to be used for the request
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
    
    #Get the indervidual dictionaries for the different transport modes
    vals = get_dist_duration(UniqueID, start, end, api_key)
    trans = get_transit_details(start, end, api_key, depature_time)
    
    #Combine them into one dictionary
    data = vals.copy()
    data.update(trans)
    
    return data

def write_to_csv(filename, row):
    """ Writes a list of direction results to a csv file.
    
    Arguements:
        filename - String - name of the file to write the results too.
        row - dictionary - dictionary containing the direction results for a post code pair
    """
    #Check if the file already exists
    if os.path.exists(filename):
        exists = True
    else:
        exists = False
        
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
    

import requests
import ConfigParser

#Get the settings from the config file
config = ConfigParser.SafeConfigParser()
config.read("Settings.cfg")

#Get the API key from the settings file
api_key = config.get('API', 'key')

#Test values
start = "TF9 1RW"
wp = ("SY3 8SN", "CH1 3AG")
end = "NE6 5DB"

mode = "driving"

def get_waypoint_string(waypoints):

    wps = ""

    for i, wp in enumerate(waypoints):
        if i == 0:
            wps = wps + wp
        else:
            wps = wps + "|" + wp

    return wps

waypoints = get_waypoint_string(wp)

r = requests.get('https://maps.googleapis.com/maps/api/directions/json?origin={}&destination={}&waypoints={}&mode={}&key={}'.format(start, end, waypoints, mode, api_key))


legs = r.json().get('routes')[0].get('legs')

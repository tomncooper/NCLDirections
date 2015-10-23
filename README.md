# NCLDirections

Scripts and tools for gathering data on commuter journeys using the [Google Directions API](https://developers.google.com/maps/documentation/directions/) and [Google GeoCoding API](https://developers.google.com/maps/documentation/geocoding/)

Methods for extracting directions from the Google API are located in `Directions.py`. The `GetData.py` script uses these methods to extract the directions data, it takes no arguments and gets its parameters from a file called `Settings.cfg` in the same directory.

The input and output file paths, as well as the Google API key, should be placed in `Settings.cfg`. An example setting file layout is shown in `Example-Settings.cfg`.

To use these scripts you will need to log onto the [Google Developer Console](https://console.developers.google.com/) and enable both the Google Maps Directions API and Google Maps Geocoding API. Then obtain a server API key and place this in the settings file. 

from geocode import getGeocodeLocation
import json
import httplib2

import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)

foursquare_client_id = "N1XUALZYEPPDJK0M5KBE23FCJUFRL1EVCOMEX3K4XTEMHUHI"
foursquare_client_secret = "VHQ2LXMDTLBUJJW4D3NR0WDKQKXY1A3DMUGFZFPUMCV1KZBE"


def findARestaurant(mealType,location):
	#1. Use getGeocodeLocation to get the latitude and longitude coordinates of the location string.
	
	#2.  Use foursquare API to find a nearby restaurant with the latitude, longitude, and mealType strings.
	#HINT: format for url will be something like https://api.foursquare.com/v2/venues/search?client_id=CLIENT_ID&client_secret=CLIENT_SECRET&v=20130815&ll=40.7,-74&query=sushi

	#3. Grab the first restaurant
	#4. Get a  300x300 picture of the restaurant using the venue_id (you can change this by altering the 300x300 value in the URL or replacing it with 'orginal' to get the original picture
	#5. Grab the first image
	#6. If no image is available, insert default a image url
	#7. Return a dictionary containing the restaurant name, address, and image url	
	lat, lon = getGeocodeLocation(location)
	url = ('https://api.foursquare.com/v2/venues/search?client_id=%s&client_secret=%s&v=20170509&ll=%s,%s&query=%s' % \
		(foursquare_client_id, foursquare_client_secret, lat, lon, mealType))

	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])

	if result['response']['venues']:
		firstOne = result['response']['venues'][0]
		restaurant_name = firstOne['name']
		
		restaurant_adderss = ""
		for each in firstOne['location']['formattedAddress']:
			restaurant_adderss += each + " "

		venue_id = firstOne['id']
		pic_url = ('https://api.foursquare.com/v2/venues/%s/photos?client_id=%s&client_secret=%s&v=20170509' % \
					(venue_id, foursquare_client_id, foursquare_client_secret))

		pic_result = json.loads(h.request(pic_url, 'GET')[1])

		if pic_result['response']['photos']['items']:
			first_pic = pic_result['response']['photos']['items'][0]
			
			restaurant_first_pic = first_pic['prefix'] + "300x300" + first_pic['suffix']
		else:
			restaurant_first_pic = "https://media-cdn.tripadvisor.com/media/photo-s/0b/50/62/2c/the-restaurant-at-the.jpg"

		restaurantInfo = {'name' : restaurant_name,
						'address' : restaurant_adderss,
						'picture': restaurant_first_pic}

		return restaurantInfo
	else:
		return "No Restaurant Found"

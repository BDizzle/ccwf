import base64
import json
import os
import ssl
import sys
import urllib.request, urllib.parse, urllib.error
from datetime import datetime
from datetime import timedelta

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

server_address = os.environ.get('ccwf_server_address', 'tighty.tv')
max_results = os.environ.get('ccwf_max_results', 10)
max_days = os.environ.get('ccwf_max_days', 7)
webflow_api_key = os.environ.get('ccwf_wf_api_key')
webflow_collection_id = os.environ.get('ccwf_wf_collection_id')

exit = True

if webflow_api_key == None:
	print("ERROR: You must set the 'ccwf_wf_api_key' environment variable")
elif webflow_collection_id == None:
	print("ERROR: You must set the 'ccwf_wf_collection_id' environment variable")
else:
	exit = False

if exit == True:
	sys.exit(1)

max_results = int(max_results)
max_days = int(max_days)

start_time = datetime.now();
end_time = start_time + timedelta(days=max_days);

query_string = urllib.parse.urlencode({
	'page_size': max_results, 
	'start': start_time, 
	'end': end_time,
	'channel': 1, 
	'include': 'show,channel,location'
})

# First, get the existing items that are on WebFlow already, we will update/insert depending if it's already in the CMS
# We also need to remove out-of-date items

cc_request_url = 'http://{0}/cablecastapi/v1/scheduleitems?{1}'.format(server_address, query_string)

# Execute the request to the server, and process the JSON document
schedule = json.load(urllib.request.urlopen(cc_request_url))

print('url: {0}'.format(cc_request_url))
print('start: {0}\nend: {1}'.format(start_time, end_time))
print('got {0} items'.format(len(schedule['scheduleItems'])))

# Go through each of the returned items, create WebFlow CMS items for each
for item in schedule['scheduleItems']:
	show_id = item['show']
	show = next(x for x in schedule['shows'] if x['id']==show_id)
	print('At {0}: {1} on {2}'.format(item['runDateTime'], show['cgTitle'], item['channel']))

	new_item = {
	'fields': {
		'name': str(item['id']), 
		'_archived': False, 
		'_draft': False,
		'show-id': show_id,
		'title': show['cgTitle'],
		'time': item['runDateTime']}}

	webflow_post_url = 'https://api.webflow.com/collections/{0}/items?live=true'.format(webflow_collection_id)

#	post_data = urllib.parse.urlencode(new_item).encode()
	post_data = json.dumps(new_item).encode('utf8')

	req = urllib.request.Request(webflow_post_url, post_data)

	req.add_header("Authorization", 'Bearer ' + webflow_api_key)
	req.add_header('accept-version', '1.0.0')
	req.add_header('Content-Type', 'application/json')

	print(new_item)

	response = ''

	try:
		response = urllib.request.urlopen(req)
		print('  Result: ' + str(response.code))
	except urllib.error.HTTPError as e:
		print('  ERROR:')
		print('    code: ' + str(e.code))
		print('    message: ' + e.msg)
		print('')







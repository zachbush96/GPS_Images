#TODO:
# 1. Once a location is deleted, the page should be refreshed (CORRECTLY!) to get a new bearer token (make sure the URL is reset) []
# 2. Ability to rename (new nick-name) a location [☑️]
# 3. Ability to erase individual images [☑️]
# 4. Ability to pull new images of every location every 48 hours [] - https://us1.make.com/210192/scenarios/2300843/edit
# 5. Backup functionality - https://chat.openai.com/share/fd1b281b-1ab1-403f-a4d7-bd6c7cdcc91a []
# 6. Think about making the from_date range dynamic and user defined []
	# How could the user define the range of the dates?
	# How does this change the output of the image? Does it just pull the most recent image?

# 7. Resize the .image-card div in the HTML to eliminate scroll bars []
# 8. Select dynamic date range for the images []
# 9. Make SURE a bearer token is generated and passed to the front end every request []
# ^^^ This is important because the bearer token expires every 30min. and sometimes the index page is pulled without a bearer token, forcing the user to pull their own bearer token
# 10. Better logging and error handling, making sure the user knows what's going on [☑️]
# 11. Use Google Docs as a backend instead of a JSON object []


from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
import time
import requests
import logging
from logging.handlers import RotatingFileHandler
import shutil
import zipfile
import sys

app = Flask(__name__)
BearerToken = ""
Client_ID = os.getenv('CLIENT_ID')
Client_Secret = os.getenv('CLIENT_SECRET')

def setupLogging():
	handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
	handler.setLevel(logging.INFO)
	formatter = logging.Formatter(
	    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	app.logger.addHandler(handler)


setupLogging()


def backup_data():
	# Define the directories and files to backup
	root_files = ['main.py', 'locations.json']
	directories = ['templates', 'static/images']

	# Create a backup folder if it doesn't exist
	backup_dir = 'backup'
	if not os.path.exists(backup_dir):
		print('Making Backup Folder')
		os.makedirs(backup_dir)
	#If the backup.zip file already exists, delete it
	if os.path.exists(backup_dir + '/backup.zip'):
		print('Deleting Backup File')
		os.remove(backup_dir + '/backup.zip')

	# Backup individual files in the root directory
	for file in root_files:
		shutil.copy(file, os.path.join(backup_dir, file))

	# Backup directories
	for directory in directories:
		destination = os.path.join(backup_dir, directory)
		if not os.path.exists(destination):
			os.makedirs(destination)
		for subdir, dirs, files in os.walk(directory):
			for file in files:
				full_file_path = os.path.join(subdir, file)
				shutil.copy(full_file_path, os.path.join(backup_dir, full_file_path))

	# Compress the backup folder into a zip file
	with zipfile.ZipFile('backup.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
		for root, dirs, files in os.walk(backup_dir):
			for file in files:
				zipf.write(
				    os.path.join(root, file),
				    os.path.relpath(os.path.join(root, file),
				                    os.path.join(backup_dir, '..')))
	print(f'Backup completed. Backup file saved as backup.zip')
	#Delete the backup folder
	shutil.rmtree(backup_dir)
	print(f'Backup folder deleted')


def get_Bearer_Token():
	try:
		url = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
		headers = {'content-type': 'application/x-www-form-urlencoded'}
		data = {
		    'grant_type': 'client_credentials',
		    'client_id': Client_ID,
		    'client_secret': Client_Secret
		}
		response = requests.post(url, headers=headers, data=data)
		response_json = response.json()
		if 'access_token' in response_json:
			bearer_token = response_json['access_token']
			#print(f'Bearer: {bearer_token}')
			return bearer_token
		else:
			raise Exception("Failed to get Bearer Token")
	except Exception as e:
		print(f"Error getting Bearer Token: {str(e)}")
		raise


locations_data_path = 'locations.json'
if not os.path.exists(
    locations_data_path):  #Create the locations.json file if it doesn't exist
	with open(locations_data_path, 'w') as file:
		json.dump([], file)


def load_locations(
):  #Load locations from the locations.json file and return a list of locations
	with open(locations_data_path, 'r') as file:
		return json.load(file)


def save_locations(locations):
	#Save the locations to the locations.json file
	with open(locations_data_path, 'w') as file:
		json.dump(locations, file)


@app.route('/')
def index():
	return render_template('index.html', generatedBearerToken=get_Bearer_Token())


@app.errorhandler(404)
def resource_not_found(e):
	return jsonify(error=str(e), message="Resource not found"), 404


@app.errorhandler(500)
def internal_error(e):
	return jsonify(error=str(e), message="Internal server error"), 500


@app.route('/upload', methods=['GET'])  #Serve the Upload Page
def upload_page():
	return render_template('upload_image.html')


@app.route('/backup', methods=['GET'])
def run_backup():
	backup_data()
	#Now that the backup.zip file is created, send the backup.zip file to the user, saved in the current working directory
	return send_from_directory(os.getcwd(), 'backup.zip', as_attachment=True)


@app.route('/add_location', methods=['POST'])
def add_location():
	# Add a new location to the locations.json file
	# The request should contain the GPS coordinates and the nickname of the location in the request body
	# The GPS coordinates should be in the format: "lat1, lon1, lat2, lon2"
	# The nickname should be a string
	try:
		data = request.get_json()
		if not data or 'gpsCoords' not in data or 'locationNickname' not in data:
			return jsonify({
			    "status": "failure",
			    "message": "Missing required fields"
			}), 400

		locations = load_locations()

		user_input_gps_coords = data['gpsCoords']
		cleaned_gps_coords = user_input_gps_coords.replace(" ", "")
		gps_coords = cleaned_gps_coords.split(",")  # gps_coords is a list

		# Validate GPS coordinates
		if len(gps_coords) != 4:
			return jsonify({
			    "status": "failure",
			    "message": "Invalid GPS coordinates"
			}), 400

		locations.append({
		    "nickname": data['locationNickname'],
		    "gpsCoords": gps_coords,
		    "images": []  # Assuming images would be added later
		})

		save_locations(locations)
		return jsonify({"status": "success", "message": "Location added"})

	except Exception as e:
		return jsonify({"status": "failure", "message": str(e)}), 500


@app.route('/locations', methods=['GET'])
def get_locations():
	# Return the list of locations in the locations.json file as a JSON response
	locations = load_locations()
	return jsonify(locations)


@app.route('/static/images/<path:filename>')
def serve_image(filename):
	return send_from_directory('static/images', filename)


@app.route('/upload_image', methods=['POST'])
def upload_image():
	# Upload an image for a specific location
	# The request should contain the image file and the nickname of the location in the request form
	# The image file should be in the 'image' field of the request and the nickname should be in the 'nick_name' field of the request
	try:
		image = request.files['image']
		nick_name = request.form['nick_name']
		file_name = f"{nick_name}.{time.strftime('%Y-%m-%d')}.jpg"
		while os.path.exists(os.path.join('static/images', file_name)):
			file_name = f"{nick_name}.{time.strftime('%Y-%m-%d-%H-%M-%S')}.jpg"
		image.save(os.path.join('static/images', file_name))
		locations = load_locations()
		for location in locations:
			if location['nickname'] == nick_name:
				location['images'].append({
				    "date": time.strftime('%Y-%m-%d'),
				    "location": f"/static/images/{file_name}"
				})
				save_locations(locations)
				break
		return jsonify({"status": "success", "message": "Image uploaded"})
	except Exception as e:
		app.logger.error(f"Error uploading image: {str(e)}")
		return jsonify({
		    "status": "failure",
		    "message": "Failed to upload image"
		}), 500


@app.route('/delete_image', methods=['POST'])
def delete_image():
	#We are recieving a POST request with a filename in the request JSON image_file_name name #We are deleting the image with the filename in the static/images folder #We are then removing the image from the location in the locations.json file
	try:
		data = request.get_json()
		if not data or 'image_file_name' not in data:
			return jsonify({
			    "status": "failure",
			    "message": "Missing required fields"
			}), 400
		image_file_name = data['image_file_name']
		OG_image_file_name = image_file_name
		#Add a leading dot to the image file name to make it a relative path
		image_file_name = f'.{image_file_name}'  #Example: ./static/images/location1.2022-01-01.jpg
		print(f"Deleting image: {image_file_name}")
		#Find the location that contains that image
		locations = load_locations()
		for location in locations:
			#print(f'Checking Location {location["nickname"]}')
			for image in location['images']:
				#print(f'          Checking Image {image["location"]}')
				if image['location'] == OG_image_file_name:
					location['images'].remove(image)
					#Delete the image file
					os.remove(image_file_name)
					save_locations(locations)
					return jsonify({"status": "success", "message": "Image deleted"})

	except Exception as e:
		return jsonify({"status": "failure", "message": str(e)}), 500


@app.route('/delete_location/<nickname>', methods=['GET'])
def delete_location(nickname):
	try:
		app.logger.info("Request received for deleting location with nickname: %s",
		                nickname)
		locations = load_locations()
		for location in locations:
			if location['nickname'] == nickname:
				locations.remove(location)
				save_locations(locations)
				app.logger.info("Location with nickname %s deleted successfully.",
				                nickname)
				return render_template('index.html')
		app.logger.warning("Location with nickname %s not found.", nickname)
		return render_template('index.html')
	except Exception as e:
		app.logger.error("Error deleting location: %s", str(e))
		return jsonify({
		    "status": "failure",
		    "message": "Failed to delete location"
		}), 500


@app.route('/automated_image_pull', methods=['GET'])
def automated_image_pull():
	print("Automated Image Pull Request Received")
	#Generate a bearer token
	bearer_token = get_Bearer_Token()
	#print("Token: " + bearer_token)
	if not bearer_token:
		print("Failed to get Bearer Token")
		return jsonify({
		    "status": "failure",
		    "message": "Failed to get Bearer Token"
		}), 500
	#Pull live images
	url = "https://services.sentinel-hub.com/api/v1/process"
	headers = {
	    "Content-Type": "application/json",
	    "Authorization": f'Bearer {bearer_token}'
	}
	from_date = time.strftime(
	    '%Y-%m-%d', time.gmtime(time.time() - 8 * 24 * 60 * 60)) + 'T00:00:00Z'
	to_date = time.strftime('%Y-%m-%d', time.gmtime(time.time())) + 'T23:59:59Z'
	locations = load_locations()
	for location in locations:
		data = {
		    "input": {
		        "bounds": {
		            "bbox": [
		                float(location["gpsCoords"][0]),
		                float(location["gpsCoords"][1]),
		                float(location["gpsCoords"][2]),
		                float(location["gpsCoords"][3])
		            ]
		        },
		        "data": [{
		            "dataFilter": {
		                "timeRange": {
		                    "from": f'{from_date}',
		                    "to": f'{to_date}'
		                }
		            },
		            "type": "sentinel-2-l2a"
		        }]
		    },
		    "output": {
		        "width":
		        512,
		        "height":
		        512,
		        "responses": [{
		            "identifier": "default",
		            "format": {
		                "type": "image/png"
		            }
		        }]
		    },
		    "evalscript":
		    "//VERSION=3\n\nfunction setup() {\n  return {\n    input: [\"B02\", \"B03\", \"B04\"],\n    output: { bands: 3 }\n  };\n}\n\nfunction evaluatePixel(sample) {\n  return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];\n}"
		}
		response = requests.post(url, headers=headers, json=data)
		if response.status_code == 200:
			print("Successfully pulled live images")
			file_name = f"{location['nickname']}.{time.strftime('%Y-%m-%d')}.jpg"
			while os.path.exists(os.path.join('static/images', file_name)):
				file_name = f"{location['nickname']}.{time.strftime('%Y-%m-%d-%H-%M-%S')}.jpg"
			with open(os.path.join('static/images', file_name), 'wb') as file:
				file.write(response.content)
			for loc in locations:
				if loc['nickname'] == location['nickname']:
					loc['images'].append({
					    "date": time.strftime('%Y-%m-%d'),
					    "location": f"/static/images/{file_name}"
					})
					save_locations(locations)
					break
		else:
			print(
			    f'Failed to pull live images. Status code: {response.status_code} | Response content: {response.content}'
			)
			return jsonify({
			    "status":
			    "failure",
			    "message":
			    f'Failed to pull live images. Status code: {response.status_code} | Response content: {response.content}'
			}), 500  # Return a failure message
	return jsonify({
	    "status": "success",
	    "message": "Live images pulled and uploaded"
	})  # Return a success message


@app.route('/pull_live_images', methods=['POST'])
def pull_live_images():
	bearer_token = request.headers.get('Authorization')
	url = "https://services.sentinel-hub.com/api/v1/process"
	headers = {
	    "Content-Type": "application/json",
	    "Authorization": f'{bearer_token}'
	}
	from_date = time.strftime(
	    '%Y-%m-%d', time.gmtime(time.time() - 8 * 24 * 60 * 60)) + 'T00:00:00Z'
	to_date = time.strftime('%Y-%m-%d', time.gmtime(time.time())) + 'T23:59:59Z'
	locations = load_locations()
	for location in locations:
		data = {
		    "input": {
		        "bounds": {
		            "bbox": [
		                float(location["gpsCoords"][0]),
		                float(location["gpsCoords"][1]),
		                float(location["gpsCoords"][2]),
		                float(location["gpsCoords"][3])
		            ]
		        },
		        "data": [{
		            "dataFilter": {
		                "timeRange": {
		                    "from": f'{from_date}',
		                    "to": f'{to_date}'
		                }
		            },
		            "type": "sentinel-2-l2a"
		        }]
		    },
		    "output": {
		        "width":
		        512,
		        "height":
		        512,
		        "responses": [{
		            "identifier": "default",
		            "format": {
		                "type": "image/png"
		            }
		        }]
		    },
		    "evalscript":
		    "//VERSION=3\n\nfunction setup() {\n  return {\n    input: [\"B02\", \"B03\", \"B04\"],\n    output: { bands: 3 }\n  };\n}\n\nfunction evaluatePixel(sample) {\n  return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];\n}"
		}
		response = requests.post(url, headers=headers, json=data)
		if response.status_code == 200:
			print("Successfully pulled live images")
			file_name = f"{location['nickname']}.{time.strftime('%Y-%m-%d')}.jpg"
			while os.path.exists(os.path.join('static/images', file_name)):
				file_name = f"{location['nickname']}.{time.strftime('%Y-%m-%d-%H-%M-%S')}.jpg"
			with open(os.path.join('static/images', file_name), 'wb') as file:
				file.write(response.content)
			for loc in locations:
				if loc['nickname'] == location['nickname']:
					loc['images'].append({
					    "date": time.strftime('%Y-%m-%d'),
					    "location": f"/static/images/{file_name}"
					})
					save_locations(locations)
					break
		else:
			return jsonify({
			    "status":
			    "failure",
			    "message":
			    f'Failed to pull live images. Status code: {response.status_code} | Response content: {response.content}'
			}), 500  # Return a failure message
	return jsonify({
	    "status": "success",
	    "message": "Live images pulled and uploaded"
	})  # Return a success message


#Route to rename locations (update nickname)
@app.route('/rename_location', methods=['POST'])
def rename_location():
	try:
		data = request.get_json()
		if not data or 'old_nickname' not in data or 'new_nickname' not in data:
			print(f'(F) Passed data: {data}')
			return jsonify({
			    "status": "failure",
			    "message": "Missing required fields"
			}), 400
		locations = load_locations()
		print(
		    f'Original Location Name: {data["old_nickname"]} | New Location Name: {data["new_nickname"]}'
		)
		for location in locations:
			if location['nickname'] == data['old_nickname']:
				location['nickname'] = data['new_nickname']
				save_locations(locations)
				return jsonify({"status": "success", "message": "Location renamed"})
		return jsonify({"status": "failure", "message": "Location not found"}), 404
	except Exception as e:
		return jsonify({"status": "failure", "message": str(e)}), 500


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80)

# Location Image Manager

This Flask application allows you to manage locations and their corresponding images. The app provides functionalities to add, rename, delete locations, upload images, pull live images from Sentinel Hub, and perform backups.

## Features
- Add a new location with GPS coordinates and a nickname.
- Rename an existing location.
- Delete a location.
- Upload images for a specific location.
- Delete individual images.
- Pull live images from Sentinel Hub every 48 hours.
- Backup functionality to save data and images.
- Logging and error handling.

## Requirements
- Python 3.x
- Flask
- Requests
- JSON
- Logging
- Shutil
- Zipfile

## Installation
1. Clone the repository:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2. Install the required dependencies:
    ```bash
    pip install flask requests
    ```

## Configuration
Replace the `Client_ID` and `Client_Secret` variables in the `main.py` file with your Sentinel Hub credentials:
```python
Client_ID = "your_client_id"
Client_Secret = "your_client_secret"
```

## Running the Application

To start the Flask application, run:\
```bash
python main.py
```
The application will be accessible at http://0.0.0.0:80.

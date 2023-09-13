import RPi.GPIO as GPIO
import time
import os
import boto3
import datetime
import logging

button_pin = 18
s3_bucket_name = 'raspberrypi4b-images'
s3 = boto3.client('s3')

GPIO.setmode(GPIO.BCM)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Counter for the batch number
batch_counter = 1

# Device ID
device_id = "000111"

# Dictionary to store the camera names and their corresponding USB port numbers
camera_usb_ports = {
    '/dev/video0': 'camera1',
    '/dev/video2': 'camera2',
    '/dev/video4': 'camera3'
}

# Configure logging
logging.basicConfig(filename='/home/rahultanwar/PythonFiles/camera_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def take_photo(camera_name):
    global batch_counter

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    timestamp_formatted = now.strftime("%Y_%m_%d_%H_%M_%S")

    logging.info(f"device_id: {device_id}, batch_counter: {batch_counter}, camera_name: {camera_name}, timestamp_formatted: {timestamp_formatted}")

    image_path = f"/home/rahultanwar/PythonFiles/{device_id}_batch{batch_counter}_{camera_name}_{timestamp_formatted}.jpeg"

    logging.info(f"Generated image_path: {image_path}")

    camera_usb_port = [usb_port for usb_port, name in camera_usb_ports.items() if name == camera_name]
    if not camera_usb_port:
        logging.error(f"Camera {camera_name} not found in the USB ports.")
        return

    try:
        os.system(f'fswebcam -d {camera_usb_port[0]} -r 1920x1080 --no-banner {image_path}')
    except Exception as e:
        logging.error(f"Failed to capture photo from {camera_name}: {str(e)}")
        return

    try:
        s3.upload_file(image_path, s3_bucket_name, f"{device_id}_batch{batch_counter}_{camera_name}_{timestamp_formatted}.jpeg")
    except Exception as e:
        logging.error(f"Failed to upload photo from {camera_name} to S3: {str(e)}")
        return

    logging.info(f"Photo captured from {camera_name} in batch {batch_counter} at {timestamp_formatted} and uploaded to S3.")

def capture_photos(channel):
    global batch_counter

    for camera_usb_port, camera_name in camera_usb_ports.items():
        take_photo(camera_name)
        
        # Wait for 5 seconds before capturing from the next camera
        time.sleep(3)

    batch_counter += 1

GPIO.add_event_detect(button_pin, GPIO.RISING, callback=capture_photos, bouncetime=300)

try:
    while True:
        time.sleep(2)
except KeyboardInterrupt:
    GPIO.cleanup()

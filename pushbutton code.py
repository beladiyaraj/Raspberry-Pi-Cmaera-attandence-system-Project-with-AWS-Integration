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

# Dictionary to store the camera names and their corresponding USB port numbers
camera_usb_ports = {
    '/dev/video0': 'camera1',
    '/dev/video1': 'camera2',
    '/dev/video2': 'camera3'
}

# Configure logging
logging.basicConfig(filename='/home/pi/PythonFiles/camera_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def take_photo(camera_name):
    global batch_counter

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    timestamp_formatted = now.strftime("%Y-%m-%d_%I-%M-%S-%p")

    image_path = f"/home/pi/PythonFiles/batch{batch_counter}_{camera_name}_{timestamp}.jpeg"

    # Get the corresponding USB port for the camera
    camera_usb_port = [usb_port for usb_port, name in camera_usb_ports.items() if name == camera_name]
    if not camera_usb_port:
        logging.error(f"Camera {camera_name} not found in the USB ports.")
        return

    # Capture photo from the specified camera's USB port
    try:
        os.system(f'fswebcam -d {camera_usb_port[0]} -r 1920x1080 --no-banner {image_path}')
    except Exception as e:
        logging.error(f"Failed to capture photo from {camera_name}: {str(e)}")
        return

    # Upload photo to S3 bucket
    try:
        s3.upload_file(image_path, s3_bucket_name, f"{camera_name}_{timestamp}.jpeg")
    except Exception as e:
        logging.error(f"Failed to upload photo from {camera_name} to S3: {str(e)}")
        return

    logging.info(f"Photo captured from {camera_name} in batch {batch_counter} at {timestamp_formatted} and uploaded to S3.")

def capture_photos(channel):
    global batch_counter

    for camera_usb_port, camera_name in camera_usb_ports.items():
        take_photo(camera_name)

    # Increment the batch counter after capturing photos from all cameras
    batch_counter += 1

GPIO.add_event_detect(button_pin, GPIO.RISING, callback=capture_photos, bouncetime=300)

try:
    while True:
        time.sleep(2)
except KeyboardInterrupt:
    GPIO.cleanup()

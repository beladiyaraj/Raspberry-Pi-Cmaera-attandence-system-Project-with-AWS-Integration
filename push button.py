import RPi.GPIO as GPIO
import time
import os
import boto3
import datetime
import logging

# GPIO Pin Setup
button_pin = 27
s3_bucket_name = 'raspberrypi4b-images'
s3 = boto3.client('s3')

GPIO.setmode(GPIO.BCM)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Using pull-up resistor

# Device ID
device_id = "000111"

# Store the camera names and their corresponding USB port numbers
camera_usb_ports = {
    '/dev/video0': 'camera1',
    '/dev/video2': 'camera2',
   # '/dev/video4': 'camera3'
}

# Configure logging
logging.basicConfig(filename='/home/rahultanwar/PythonFiles/camera_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Flag to control capture within debounce period
is_capturing = False


def save_batch_counter():
    with open('/home/rahultanwar/PythonFiles/batch_counter.txt', 'w') as file:
        file.write(str(batch_counter))


def load_batch_counter():
    try:
        with open('/home/rahultanwar/PythonFiles/batch_counter.txt', 'r') as file:
            return int(file.read())
    except FileNotFoundError:
        return 1


# Initialize the batch counter by loading from file
batch_counter = load_batch_counter()


def take_photo(camera_name):
    global batch_counter
    now = datetime.datetime.now()
    timestamp_formatted = now.strftime("%Y_%m_%d_%H_%M_%S")

    logging.info(
        f"device_id: {device_id}, batch_counter: {batch_counter}, camera_name: {camera_name}, timestamp_formatted: {timestamp_formatted}")

    image_path = f"/home/rahultanwar/PythonFiles/{device_id}batch{batch_counter}{camera_name}_{timestamp_formatted}.jpeg"

    camera_usb_port = [usb_port for usb_port,
                       name in camera_usb_ports.items() if name == camera_name]
    if not camera_usb_port:
        logging.error(f"Camera {camera_name} not found in the USB ports.")
        return

    try:
        os.system(
            f'fswebcam -d {camera_usb_port[0]} -r 1920x1080 --no-banner {image_path}')
    except Exception as e:
        logging.error(f"Failed to capture photo from {camera_name}: {str(e)}")
        return

    try:
        s3.upload_file(image_path, s3_bucket_name,
                       f"{device_id}batch{batch_counter}{camera_name}_{timestamp_formatted}.jpeg")
    except Exception as e:
        logging.error(
            f"Failed to upload photo from {camera_name} to S3: {str(e)}")
        return

    logging.info(f"Photo captured and uploaded to S3: {image_path}")


def capture_photos():
    global batch_counter, is_capturing

    logging.info(f"Button pressed detected. is_capturing: {is_capturing}")

    if is_capturing:
        logging.info(
            "Capture already in progress. Ignoring this button press.")
        return

    logging.info("Starting photo capture process.")
    is_capturing = True

    for camera_usb_port, camera_name in camera_usb_ports.items():
        take_photo(camera_name)
        # Wait for 3 seconds before capturing from the next camera
        time.sleep(5)

    batch_counter += 1
    save_batch_counter()  # Save the updated batch_counter immediately after increment
    logging.info(
        f"Photo capture completed for batch {batch_counter}. Incrementing batch_counter.")

    # Delay to ensure no re-triggering happens immediately
    time.sleep(1)  # You may adjust this based on your observation
    is_capturing = False
    logging.info(
        "Reset is_capturing flag and ready for the next button press.")

try:
    while True:
        button_state = GPIO.input(button_pin)
        if button_state == False:  # Button is pressed
            capture_photos()  # Call the function to handle photo capture
            time.sleep(0.5)  # Debounce delay; adjust as necessary
        time.sleep(0.1)  # Short delay to reduce CPU usage
except KeyboardInterrupt:
    GPIO.cleanup()  # Clean up GPIO settings
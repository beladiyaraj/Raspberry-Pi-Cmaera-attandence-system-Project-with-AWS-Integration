# Import necessary libraries
import boto3  # AWS SDK for Python to use AWS services like Rekognition and S3
import re  # Regular expression library for string matching
import mysql.connector  # MySQL database connector to interact with MySQL database
import logging  # Logging library to log messages
import os  # OS library to interact with the operating system, like reading environment variables
from io import BytesIO  # BytesIO for in-memory binary streams
from PIL import Image  # Python Imaging Library to work with images
from datetime import datetime  # Datetime library for handling date and time

# Initialize logging to capture and log messages for debugging and tracking
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS service clients for Rekognition and S3
rekognition_client = boto3.client('rekognition')
s3_client = boto3.client('s3')

# Read database credentials from environment variables for security
DB_HOST = os.environ['DB_HOST']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_DATABASE = os.environ['DB_DATABASE']

def detect_number_plate(bucket_name, image_key):
    """
    Detects text in an image stored in an S3 bucket that resembles a vehicle's number plate.

    :param bucket_name: Name of the S3 bucket where the image is stored.
    :param image_key: The key (path) to the image file in the S3 bucket.
    :return: A string containing the detected number plate text. If error occurs, returns an empty string.
    """
    # Log the action of detecting a number plate
    logger.info(f"Detecting number plate for image: {image_key} in bucket: {bucket_name}")
    try:
        # Use AWS Rekognition to detect text in the image
        response = rekognition_client.detect_text(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': image_key}}
        )
        # Compile detected text that is classified as 'LINE' which might represent number plates
        detected_text = ' '.join([text['DetectedText'] for text in response['TextDetections'] if text['Type'] == 'LINE'])
        # Log the detected text
        logger.info(f"Detected number plate text: {detected_text}")
        return detected_text
    except Exception as e:
        # Log any errors that occur during the detection process
        logger.error(f"An error occurred in detect_number_plate: {str(e)}")
        return ""

def detect_photo_id_text(bucket_name, image_key):
    """
    Detects text in an image stored in an S3 bucket that resembles text on a photo ID.

    :param bucket_name: Name of the S3 bucket where the image is stored.
    :param image_key: The key (path) to the image file in the S3 bucket.
    :return: A string containing the detected photo ID text. If an error occurs, returns an empty string.
    """
    # Log the action of detecting photo ID text
    logger.info(f"Detecting photo ID text for image: {image_key} in bucket: {bucket_name}")
    try:
        # Use AWS Rekognition to detect text in the image
        response = rekognition_client.detect_text(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': image_key}}
        )
        # Compile detected text that is classified as 'LINE', likely representing ID text
        detected_text = ' '.join([text['DetectedText'] for text in response['TextDetections'] if text['Type'] == 'LINE'])
        # Log the detected text
        logger.info(f"Detected photo ID text: {detected_text}")
        return detected_text
    except Exception as e:
        # Log any errors that occur during the detection process
        logger.error(f"An error occurred in detect_photo_id_text: {str(e)}")
        return ""

def detect_and_crop_face(bucket_name, image_key):
    """
    Detects faces in an image stored in an S3 bucket and crops the first detected face from the image.

    :param bucket_name: Name of the S3 bucket where the image is stored.
    :param image_key: The key (path) to the image file in the S3 bucket.
    :return: A byte array of the cropped face image. If no face is detected or an error occurs, returns an empty byte array.
    """
    # Log the action of detecting and cropping a face from the image
    logger.info(f"Detecting face for image: {image_key} in bucket: {bucket_name}")
    try:
        # Use AWS Rekognition to detect faces in the image
        response = rekognition_client.detect_faces(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': image_key}}
        )
        # Retrieve the image from S3
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=image_key)
        img = Image.open(BytesIO(s3_response['Body'].read()))

        # Check if any faces were detected
        if len(response['FaceDetails']) > 0:
            # Get bounding box of the first detected face
            box = response['FaceDetails'][0]['BoundingBox']
            # Calculate coordinates of the bounding box relative to the image size
            x1 = int(box['Left'] * img.width)
            y1 = int(box['Top'] * img.height)
            x2 = int((box['Left'] + box['Width']) * img.width)
            y2 = int((box['Top'] + box['Height']) * img.height)
            # Crop the image to the bounding box
            img_cropped = img.crop((x1, y1, x2, y2))
            # Convert cropped image to byte array
            img_byte_arr = BytesIO()
            img_cropped.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
        else:
            # Log if no face is detected
            logger.error("No face detected")
            img_byte_arr = b''
        return img_byte_arr
    except Exception as e:
        # Log any errors that occur during the face detection and cropping process
        logger.error(f"An error occurred in detect_and_crop_face: {str(e)}")
        return b''

def update_or_insert_db(cursor, conn, device_id, batch_id, camera_number, bucket_name, file_name, year, month, date, hours, minutes, seconds):
    """
    Updates or inserts a record in the database based on the detected information from images.

    :param cursor: The MySQL cursor object for executing database queries.
    :param conn: The MySQL connection object for database transactions.
    :param device_id: The device identifier from which the images are captured.
    :param batch_id: A unique identifier for the batch of images.
    :param camera_number: Identifies the camera that captured the image.
    :param bucket_name: The name of the S3 bucket containing the images.
    :param file_name: The file name of the image in the S3 bucket.
    :param year: Year component of the image capture timestamp.
    :param month: Month component of the image capture timestamp.
    :param date: Date component of the image capture timestamp.
    :param hours: Hours component of the image capture timestamp.
    :param minutes: Minutes component of the image capture timestamp.
    :param seconds: Seconds component of the image capture timestamp.
    """
    # Convert year, month, and date to integers and compute the day of the week for the given date
    computed_day = datetime(int(year), int(month), int(date)).strftime('%A')

    # Start database update or insertion process
    logger.info("Starting update_or_insert_db")
    try:
        # Check if there is already an entry for this batch_id
        cursor.execute("SELECT * FROM trans WHERE batch_id = %s", (batch_id,))
        row = cursor.fetchone()

        if row:
            # If an entry exists, update the specific field based on camera_number
            if camera_number == '1':
                # Camera 1 captures visitor ID details
                sql = "UPDATE trans SET visitor_ID_Details = %s WHERE batch_id = %s"
                cursor.execute(sql, (detect_photo_id_text(bucket_name, file_name), batch_id))
            elif camera_number == '2':
                # Camera 2 captures visitor image thumbnails
                sql = "UPDATE trans SET visitor_image_thumbnail = %s WHERE batch_id = %s"
                cursor.execute(sql, (detect_and_crop_face(bucket_name, file_name), batch_id))
            elif camera_number == '3':
                # Camera 3 captures vehicle numbers
                sql = "UPDATE trans SET vehicle_no = %s WHERE batch_id = %s"
                cursor.execute(sql, (detect_number_plate(bucket_name, file_name), batch_id))
        else:
            # If no entry exists, create a new one with the detected details
            logger.info(f"No existing entry found for batch_id: {batch_id}. Creating a new one.")

            # Default values for fields, to be filled based on camera_number
            visitor_ID_Details = None
            visitor_image_thumbnail = None
            vehicle_no = None

            # Populate the specific field based on the camera number
            if camera_number == '1':
                visitor_ID_Details = detect_photo_id_text(bucket_name, file_name)
            elif camera_number == '2':
                visitor_image_thumbnail = detect_and_crop_face(bucket_name, file_name)
            elif camera_number == '3':
                vehicle_no = detect_number_plate(bucket_name, file_name)
                
            # SQL query to insert a new record
            sql = """INSERT INTO trans (device_id, batch_id, visitor_ID_Details, visitor_image_thumbnail, vehicle_no, year, month, date, day, hours, minutes, seconds)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (device_id, batch_id, visitor_ID_Details, visitor_image_thumbnail, vehicle_no, year, month, date, computed_day, hours, minutes, seconds))
        
        # Commit the transaction to make changes persistent
        conn.commit()
        logger.info("Database operation completed successfully.")
    except Exception as e:
        # Log any errors that occur during the database operation
        logger.error(f"An error occurred during database operation: {str(e)}")

def lambda_handler(event, context):
    """
    AWS Lambda function handler to process images uploaded to an S3 bucket.

    :param event: Event data that triggered the Lambda function.
    :param context: Runtime information provided by AWS Lambda.
    :return: A dictionary containing the status code and body message.
    """
    # Log the start of the Lambda function handler
    logger.info("Starting lambda_handler")

    # Extract file name and bucket name from the event that triggered the Lambda function
    file_name = event['Records'][0]['s3']['object']['key']
    bucket_name = event['Records'][0]['s3']['bucket']['name']

    # Regular expression to parse the file name for required components
    match = re.match(r'(\d{6})batch(\d+)camera(\d+)_(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})\.jpeg', file_name)

    # Validate the file name format
    if not match:
        # Log an error if the file name does not match the expected format
        logger.error(f"Filename format mismatch: {file_name}")
        return {
            'statusCode': 400,
            'body': 'Filename format mismatch'
        }

    # If the file name format is valid, extract components from the file name
    if match:
        device_id, batch_id, camera_number, year, month, date, hours, minutes, seconds = match.groups()
        # Ensure device_id is properly formatted
        device_id = device_id.zfill(6)

    # Establish a connection to the MySQL database
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE
    )
    
    try:
        # Create a cursor for executing database queries
        cursor = conn.cursor(dictionary=True)
        # Perform the database update or insertion based on the detected information
        update_or_insert_db(cursor, conn, device_id, batch_id, camera_number, bucket_name, file_name, year, month, date, hours, minutes, seconds)
        
    except Exception as e:
        # Log any errors encountered when interacting with the database
        logger.error(f"Database error: {str(e)}")
    
    finally:
        # Close the cursor and database connection
        cursor.close()
        conn.close()
        logger.info("Cursor and connection closed.") 

    # Return a successful response after processing the data
    return {
        'statusCode': 200,
        'body': 'Data Processed Successfully!'
    }

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

def normalize_text(text):
    """Normalize text by removing non-alphanumeric characters and converting to uppercase."""
    return re.sub(r'\W+', '', text).upper()

def extract_name_details(text):
    """Extract name details from the given text after 'Name' keyword."""
    name_match = re.search(r"Name:?[\s-]*(\w+)", text, re.IGNORECASE)
    if name_match:
        # Extract the name and normalize it
        name_details = name_match.group(1)
        return normalize_text(name_details)
    return None

def process_exit(conn, cursor, device_id, extracted_text, exit_time):
    # Assuming extracted_text handling is correct and focusing on visitor_id_details being None...
    new_name_details = extract_name_details(extracted_text)

    if new_name_details:
        logger.info(f"Extracted Name for comparison: {new_name_details}")

        cursor.execute("""
            SELECT batch_id, visitor_id_details
            FROM trans
            WHERE device_id = %s AND exit_time IS NULL
        """, (device_id,))
        logger.info(f"Searching for matching records with device_id={device_id} and NULL exit time...")

        for row in cursor.fetchall():
            if row['visitor_id_details']:
                existing_name_details = extract_name_details(row['visitor_id_details'])
                if existing_name_details and new_name_details[:10] == existing_name_details[:10]:
                    logger.info(f"Name match found. Updating exit time for batch_id={row['batch_id']} and the exit time is:{exit_time}")
                    cursor.execute("""
                        UPDATE trans
                        SET exit_time = %s
                        WHERE device_id = %s AND batch_id = %s
                    """, (exit_time, device_id, row['batch_id']))
                    conn.commit()
                    return True
            else:
                logger.info("Record has no visitor_id_details. Skipping comparison.")

    else:
        logger.warning("No 'Name' found in the extracted text for exit processing.")
    
    logger.info("No matching record found for exit. Proceeding with usual workflow.")
    return False


def update_or_insert_db(cursor, conn, device_id, batch_id, camera_number, bucket_name, file_name, date, entry_time):
    """
    Updates or inserts a record in the database based on the detected information from images.
    Ensures that all records with the same batch_id have the same entry_time.
    """
    # Convert year, month, and date to integers and compute the day of the week for the given date
    computed_day = datetime.strptime(date, '%Y-%m-%d').strftime('%A')

    logger.info("Starting update_or_insert_db")
    try:
        # Check if there is already an entry for this batch_id
        cursor.execute("SELECT entry_time FROM trans WHERE batch_id = %s", (batch_id,))
        row = cursor.fetchone()

        # If there's already an entry for this batch_id, use the entry_time from that record
        if row:
            entry_time = row['entry_time']  # This sets entry_time to the first recorded entry_time for this batch_id

        # Execute the appropriate action based on camera_number
        if camera_number == '1':
            # Camera 1 captures visitor ID details
            visitor_id_details = detect_photo_id_text(bucket_name, file_name)
            if row:
                # Update existing record
                sql = "UPDATE trans SET visitor_ID_Details = %s WHERE batch_id = %s"
                cursor.execute(sql, (visitor_id_details, batch_id))
            else:
                # Insert new record
                insert_new_record(cursor, device_id, batch_id, date, computed_day, entry_time, visitor_id_details, None, None)
        elif camera_number == '2':
            # Camera 2 captures visitor image thumbnails
            visitor_image_thumbnail = detect_and_crop_face(bucket_name, file_name)
            if row:
                # Update existing record
                sql = "UPDATE trans SET visitor_image_thumbnail = %s WHERE batch_id = %s"
                cursor.execute(sql, (visitor_image_thumbnail, batch_id))
            else:
                # Insert new record
                insert_new_record(cursor, device_id, batch_id, date, computed_day, entry_time, None, None, visitor_image_thumbnail)
        elif camera_number == '3':
            # Camera 3 captures vehicle numbers
            vehicle_no = detect_number_plate(bucket_name, file_name)
            if row:
                # Update existing record
                sql = "UPDATE trans SET vehicle_no = %s WHERE batch_id = %s"
                cursor.execute(sql, (vehicle_no, batch_id))
            else:
                # Insert new record
                insert_new_record(cursor, device_id, batch_id, date, computed_day, entry_time, None, vehicle_no, None)

        # Commit the transaction to make changes persistent
        conn.commit()
        logger.info("Database operation completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during database operation: {str(e)}")
        conn.rollback()

def insert_new_record(cursor, device_id, batch_id, date, day, entry_time, visitor_id_details, vehicle_no, visitor_image_thumbnail):
    """
    Inserts a new record into the database with the given details.
    """
    sql = """
    INSERT INTO trans
    (device_id, batch_id, date, day, entry_time, visitor_ID_Details, vehicle_no, visitor_image_thumbnail)
    VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (device_id, batch_id, date, day, entry_time, visitor_id_details, vehicle_no, visitor_image_thumbnail))

def lambda_handler(event,context):
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
        date=year+"-"+month+"-"+date
        entry_time=hours+":"+minutes+":"+seconds

    # Establish a connection to the MySQL database
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE
    )
    # Create a cursor for executing database queries
    cursor = conn.cursor(dictionary=True)
    if camera_number == '1':
        logger.info(f"Camera 1 detected. Processing image for exit: {file_name}")
        exit_time = entry_time  # Assuming the photo name has the exit time in the same format

        extracted_text = detect_photo_id_text(bucket_name, file_name)
        if not extracted_text:
            logger.error("Failed to extract text for exit processing.")
        else:
            if process_exit(conn,cursor, device_id, extracted_text, exit_time):
                logger.info("Exit processed successfully.")
                cursor.close()
                conn.close()
                return {
                    'statusCode': 200,
                    'body': 'Exit processed successfully.'
                }
            else:
                logger.info("Exit workflow did not find a match. Continuing with usual workflow.")
    else:
        try:
            # Perform the database update or insertion based on the detected information
            update_or_insert_db(cursor, conn, device_id, batch_id, camera_number, bucket_name, file_name,date, entry_time)
            
        except Exception as e:
            # Log any errors encountered when interacting with the database
            logger.error(f"Database error: {str(e)}")
        
        finally:
            # Close the cursor and database connection
            cursor.close()
            conn.close()
            logger.info("Cursor and connection closed.") 
    try:
        # Perform the database update or insertion based on the detected information
        update_or_insert_db(cursor, conn, device_id, batch_id, camera_number, bucket_name, file_name,date, entry_time)
            
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

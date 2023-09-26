import boto3
import re
import mysql.connector
import logging
import os
from io import BytesIO
from PIL import Image
from datetime import datetime

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS services
rekognition_client = boto3.client('rekognition')
s3_client = boto3.client('s3')

# Database credentials from environment variables
DB_HOST = os.environ['DB_HOST']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_DATABASE = os.environ['DB_DATABASE']

def detect_number_plate(bucket_name, image_key):
    logger.info(f"Detecting number plate for image: {image_key} in bucket: {bucket_name}")
    try:
        response = rekognition_client.detect_text(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': image_key}}
        )
        detected_text = ' '.join([text['DetectedText'] for text in response['TextDetections'] if text['Type'] == 'LINE'])
        logger.info(f"Detected number plate text: {detected_text}")
        return detected_text
    except Exception as e:
        logger.error(f"An error occurred in detect_number_plate: {str(e)}")
        return ""

def detect_photo_id_text(bucket_name, image_key):
    logger.info(f"Detecting photo ID text for image: {image_key} in bucket: {bucket_name}")
    try:
        response = rekognition_client.detect_text(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': image_key}}
        )
        detected_text = ' '.join([text['DetectedText'] for text in response['TextDetections'] if text['Type'] == 'LINE'])
        logger.info(f"Detected photo ID text: {detected_text}")
        return detected_text
    except Exception as e:
        logger.error(f"An error occurred in detect_photo_id_text: {str(e)}")
        return ""

def detect_and_crop_face(bucket_name, image_key):
    logger.info(f"Detecting face for image: {image_key} in bucket: {bucket_name}")
    try:
        response = rekognition_client.detect_faces(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': image_key}}
        )
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=image_key)
        img = Image.open(BytesIO(s3_response['Body'].read()))

        if len(response['FaceDetails']) > 0:
            box = response['FaceDetails'][0]['BoundingBox']
            x1 = int(box['Left'] * img.width)
            y1 = int(box['Top'] * img.height)
            x2 = int((box['Left'] + box['Width']) * img.width)
            y2 = int((box['Top'] + box['Height']) * img.height)
            img_cropped = img.crop((x1, y1, x2, y2))
            img_byte_arr = BytesIO()
            img_cropped.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
        else:
            logger.error("No face detected")
            img_byte_arr = b''

        return img_byte_arr
    except Exception as e:
        logger.error(f"An error occurred in detect_and_crop_face: {str(e)}")
        return b''

def update_or_insert_db(cursor, conn, device_id, batch_id, camera_number, bucket_name, file_name, year, month, date, hours, minutes, seconds):
    # Convert year, month, and date to integers and compute the day of the week
    computed_day = datetime(int(year), int(month), int(date)).strftime('%A')

    # Check if this batch already has an entry
    logger.info("Starting update_or_insert_db")
    try:
        cursor.execute("SELECT * FROM trans WHERE batch_id = %s", (batch_id,))
        row = cursor.fetchone()

        if row:
            # Update the existing row
            if camera_number == '1':
                sql = "UPDATE trans SET visitor_ID_Details = %s WHERE batch_id = %s"
                cursor.execute(sql, (detect_photo_id_text(bucket_name, file_name), batch_id))
            elif camera_number == '2':
                sql = "UPDATE trans SET visitor_image_thumbnail = %s WHERE batch_id = %s"
                cursor.execute(sql, (detect_and_crop_face(bucket_name, file_name), batch_id))
            elif camera_number == '3':
                sql = "UPDATE trans SET vehicle_no = %s WHERE batch_id = %s"
                cursor.execute(sql, (detect_number_plate(bucket_name, file_name), batch_id))
        else:
            # Insert a new row
            logger.info(f"No existing entry found for batch_id: {batch_id}. Creating a new one.")

            # Initialize to NULL or default values
            visitor_ID_Details = None
            visitor_image_thumbnail = None
            vehicle_no = None

            # Populate specific field based on the camera_number
            if camera_number == '1':
                visitor_ID_Details = detect_photo_id_text(bucket_name, file_name)
            elif camera_number == '2':
                visitor_image_thumbnail = detect_and_crop_face(bucket_name, file_name)
            elif camera_number == '3':
                vehicle_no = detect_number_plate(bucket_name, file_name)
                
            sql = """INSERT INTO trans (device_id, batch_id, visitor_ID_Details, visitor_image_thumbnail,vehicle_no, year, month, date, day, hours, minutes, seconds)
                 VALUES (%s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

            cursor.execute(sql, (device_id, batch_id, visitor_ID_Details, visitor_image_thumbnail, vehicle_no, year, month,date, computed_day, hours, minutes, seconds))
        
        conn.commit()
        logger.info("Database operation completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during database operation: {str(e)}")

def lambda_handler(event, context):
    logger.info("Starting lambda_handler")

    file_name = event['Records'][0]['s3']['object']['key']
    bucket_name = event['Records'][0]['s3']['bucket']['name']

    match = re.match(r'(\d{6})batch(\d+)camera(\d+)_(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})\.jpeg', file_name)

    if not match:
        logger.error(f"Filename format mismatch: {file_name}")
        return {
            'statusCode': 400,
            'body': 'Filename format mismatch'
        }

    if match:
        device_id, batch_id, camera_number, year, month, date, hours, minutes, seconds = match.groups()
        device_id = device_id.zfill(6)

    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE
    )
    
    try:
        cursor = conn.cursor(dictionary=True)
        update_or_insert_db(cursor, conn, device_id, batch_id, camera_number, bucket_name, file_name, year, month, date, hours, minutes, seconds)
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
    
    finally:
        cursor.close()
        conn.close()
        logger.info("Cursor and connection closed.") 

    return {
        'statusCode': 200,
        'body': 'Data Processed Successfully!'
    }

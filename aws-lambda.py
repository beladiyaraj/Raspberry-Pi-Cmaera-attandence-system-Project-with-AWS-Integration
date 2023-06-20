import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError
from PIL import Image
import io

rekognition_client = boto3.client('rekognition')
s3_client = boto3.client('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            image_key = record['s3']['object']['key']
            image_type = image_key.split('_')[0]  # Extract the image type from the key

            logger.info(f"Processing image: {image_key}")

            # Make the API call based on the image type
            if image_type == 'camera1':
                result = detect_number_plate(bucket_name, image_key)
                save_text_to_s3(result, 'raspberrypi4b-images-output', f'{image_key.rsplit(".", 1)[0]}.txt')
            elif image_type == 'camera2':
                result = detect_person_face(bucket_name, image_key)
                save_image_to_s3(result, 'raspberrypi4b-images-output', f'{image_key.rsplit(".", 1)[0]}.jpeg')
            elif image_type == 'camera3':
                result = detect_photo_id_text(bucket_name, image_key)
                save_text_to_s3(result, 'raspberrypi4b-images-output', f'{image_key.rsplit(".", 1)[0]}.txt')

        return {
            'statusCode': 200,
            'body': 'API calls completed'
        }
    except (BotoCoreError, ClientError) as e:
        logger.error(f"An error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Internal server error'
        }

def detect_number_plate(bucket_name, image_key):
    try:
        response = rekognition_client.detect_text(
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': image_key
                }
            }
        )

        # Process the response for number plate recognition
        detected_text = []
        for text in response['TextDetections']:
            if text['Type'] == 'LINE':
                detected_text.append(text['DetectedText'])

        logger.info(f"Detected number plate text: {detected_text}")

        return detected_text
    except (BotoCoreError, ClientError) as e:
        logger.error(f"An error occurred: {str(e)}")
        return []

def detect_person_face(bucket_name, image_key):
    try:
        response = rekognition_client.detect_faces(
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': image_key
                }
            },
            Attributes=['DEFAULT']
        )

        # Process the response for person face detection
        face_details = response['FaceDetails']

        logger.info(f"Detected {len(face_details)} faces in the image")

        return face_details
    except (BotoCoreError, ClientError) as e:
        logger.error(f"An error occurred: {str(e)}")
        return []

def detect_photo_id_text(bucket_name, image_key):
    try:
        response = rekognition_client.detect_text(
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': image_key
                }
            }
        )

        # Process the response for photo ID text recognition
        detected_text = []
        for text in response['TextDetections']:
            if text['Type'] == 'LINE':
                detected_text.append(text['DetectedText'])

        logger.info(f"Detected photo ID text: {detected_text}")

        return detected_text
    except (BotoCoreError, ClientError) as e:
        logger.error(f"An error occurred: {str(e)}")
        return []

def save_text_to_s3(data, bucket_name, file_name):
    try:
        text_data = '\n'.join(data)

        s3_client.put_object(
            Body=text_data,
            Bucket=bucket_name,
            Key=file_name
        )

        logger.info(f"Text data saved to S3: {bucket_name}/{file_name}")
    except (BotoCoreError, ClientError) as e:
        logger.error(f"An error occurred while saving text data to S3 for file {file_name}: {str(e)}")


def save_image_to_s3(face_details, bucket_name, file_name):
    try:
        for i, face_detail in enumerate(face_details):
            # Fetch the bounding box coordinates
            bounding_box = face_detail['BoundingBox']

            # Fetch the original image from the source bucket
            image_object = s3_client.get_object(Bucket='raspberrypi4b-images', Key=file_name)
            image_bytes = image_object['Body'].read()

            # Open the image using PIL
            image = Image.open(io.BytesIO(image_bytes))

            # Calculate the image dimensions
            image_width, image_height = image.size

            # Calculate the crop coordinates
            left = int(bounding_box['Left'] * image_width)
            top = int(bounding_box['Top'] * image_height)
            width = int(bounding_box['Width'] * image_width)
            height = int(bounding_box['Height'] * image_height)

            # Crop the image
            cropped_image = image.crop((left, top, left + width, top + height))

            # Save the cropped image to the output bucket
            with io.BytesIO() as output_bytes:
                cropped_image.save(output_bytes, format='JPEG')
                output_bytes.seek(0)
                s3_client.put_object(
                    Body=output_bytes,
                    Bucket='raspberrypi4b-images-output',
                    Key=f"{file_name}_{i+1}.jpg"
                )

        logger.info(f"Images saved to S3: raspberrypi4b-images-output/{file_name}_{i+1}.jpg")
    except (BotoCoreError, ClientError) as e:
        error_message = f"An error occurred while saving images to S3 for file {file_name}: {str(e)}"
        if isinstance(e, ClientError) and e.response['Error']['Code'] == 'NoSuchKey':
            error_message += f". Key: {file_name}"
        logger.error(error_message)

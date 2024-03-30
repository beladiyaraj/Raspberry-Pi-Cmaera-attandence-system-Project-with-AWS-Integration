import os
import json
import boto3
from botocore.exceptions import ClientError
import mysql.connector
from datetime import datetime, timedelta
import logging
from dateutil import tz

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables for database connection
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Environment variable for SES sender email
SES_SENDER_EMAIL = os.getenv('SES_SENDER_EMAIL')

# Initialize boto3 SES client
ses_client = boto3.client('ses')

def send_email(recipient_email, subject, body):
    logger.info("Function send_email called.")
    logger.info(f"Sending email to {recipient_email} with subject: {subject}")
    try:
        response = ses_client.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={'ToAddresses': [recipient_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {'Text': {'Data': body, 'Charset': 'UTF-8'}},
            },
        )
        logger.info(f"SES send_email response: {response}")
    except ClientError as e:
        logger.error(f"SES ClientError: {e.response}")
        raise

def check_and_send_messages(cursor,connection):
    logger.info("Function check_and_send_messages called.")
    # Assuming local_time is the current time in IST
    local_time = datetime.now(tz.gettz('Asia/Dubai'))

    # Calculating "two hours ago"
    two_hours_ago = local_time - timedelta(hours=2)
    two_hours_ago_time_str = two_hours_ago.strftime('%H:%M:%S')

    # Formatting today's date
    today_date_str = local_time.strftime('%Y-%m-%d')

    logger.info(f"Time two hours ago in IST (HH:MM:SS) and the date is: {two_hours_ago_time_str} and {today_date_str}")
    logger.info("Querying customer_master table.")
    customer_query = "SELECT customer_id, device_id, contact_person_emailID FROM customer_master"
    cursor.execute(customer_query)
    customer_devices = {}
    logger.info("Fetching customer_master data.")
    customer_data = cursor.fetchall()
    logger.info(f"Fetched data: {customer_data}")
    for customer_id, device_id_json, contact_email in customer_data:
        logger.info(f"Processing customer ID: {customer_id}")
        try:
            device_ids = json.loads(device_id_json)
            logger.info(f"Device IDs for customer {customer_id}: {device_ids}")
            for device_id in device_ids:
                # Convert device_id to integer before using it as a key
                customer_devices[int(device_id)] = contact_email
        except json.JSONDecodeError:
            logger.error(f"JSON decoding error for customer {customer_id}")
        except ValueError:
            logger.error(f"Value error for customer {customer_id}, device ID: {device_id}")

    logger.info("Querying trans table with date and email_sent filter.")
    trans_query = """
    SELECT device_id,batch_id, entry_time
    FROM trans
    WHERE exit_time IS NULL 
    AND entry_time <= %s
    AND email_sent = 0
    """
    cursor.execute(trans_query, (two_hours_ago_time_str,))
    trans_data = cursor.fetchall()
    logger.info(f"Trans table data: {trans_data}")

    for (device_id,batch_id, entry_time) in trans_data:
        logger.info(f"Processing trans table device ID: {device_id} and the customer_devices are {customer_devices}")
        # Make sure to convert device_id to integer before comparison
        if int(device_id) in customer_devices:
            contact_email = customer_devices[int(device_id)]
            logger.info(f"Device ID {device_id} found in customer_devices.")

            device_id_json = json.dumps([str(device_id)])  # Ensure device_id is converted to string and then to JSON array format
            # device_id_json=json.dumps([str(111)]) 
            location_query = """
            SELECT lm.project_name, lm.building_name
            FROM location_master lm
            WHERE JSON_CONTAINS(lm.device_id, %s)
            """
            cursor.execute(location_query, (device_id_json,))
            location_info = cursor.fetchone()

            logger.info(f"Location info: {location_info}")

            project_name, building_name = location_info if location_info else ("Unknown", "Unknown")
            logger.info(f"Location info for device ID {device_id}: Project Name - {project_name}, Building Name - {building_name}")

            # Assuming contact_email is determined before this code block
            subject = "Gatex Visitor Alert !"
            body = f"""\
            Gatex Visitor Alert !
            
            A person is inside of Batch ID: {batch_id}
            Project Name: {project_name}, 
            Building Name: {building_name} 
            
            for more than 2 hours.
            """

            project_name, building_name = location_info if location_info else ("Unknown", "Unknown")
            send_email(contact_email, subject, body)

            # Update email_sent to 1 for the current record
            update_query = """
            UPDATE trans
            SET email_sent = 1
            WHERE device_id = %s AND entry_time = %s
            """
            cursor.execute(update_query, (device_id, entry_time))
            logger.info(f"Updated email_sent for device ID: {device_id}, entry time: {entry_time}")
            connection.commit()



def lambda_handler(event, context):
    logger.info("Lambda handler called.")
    connection = None
    try:
        logger.info("Connecting to the database.")
        connection = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        logger.info("Database connection established.")

        with connection.cursor() as cursor:
            logger.info("Cursor created.")
            check_and_send_messages(cursor,connection)  # Pass the IST datetime object to the function
            logger.info("Function check_and_send_messages executed.")
    except Exception as e:
        logger.error(f"Exception in lambda_handler: {e}")
        return {'statusCode': 500, 'body': json.dumps('Error processing your request.')}
    finally:
        if connection and connection.is_connected():
            logger.info("Closing database connection.")
            connection.close()

    logger.info("Lambda function execution complete.")
    return {'statusCode': 200, 'body': json.dumps('Process completed successfully!')}
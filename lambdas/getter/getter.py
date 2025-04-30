import os
import json
import boto3
import logging
from botocore.exceptions import ClientError
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

TABLE_NAME = os.environ.get("JOB_STATUS_TABLE_NAME")
dynamodb = boto3.resource('dynamodb')
job_table = dynamodb.Table(TABLE_NAME)

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 == 0:
                return int(o)
            else:
                return float(o)
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    try:
        job_id = event.get('pathParameters', {}).get('jobId')

        logger.info(f"Attempting to retrieve job status for jobId: {job_id}")
        response = job_table.get_item(Key={'jobId': job_id})

        if 'Item' in response:
            item = response['Item']
            logger.info(f"Found item for jobId: {job_id}. Status: {item.get('status')}")
            return {
                'statusCode': 200,
                'headers': { 'Content-Type': 'application/json' },
                'body': json.dumps(item, cls=DecimalEncoder)
            }
        else:
            logger.warning(f"No item found for jobId: {job_id}")
            return {
                'statusCode': 404,
                'headers': { 'Content-Type': 'application/json' },
                'body': json.dumps({'error': 'Job not found'})
            }

    except ClientError as e:
        logger.error(f"DynamoDB error retrieving job {job_id}: {e.response['Error']['Message']}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': { 'Content-Type': 'application/json' },
            'body': json.dumps({'error': 'Failed to retrieve job status due to database error'})
        }
    except Exception as e:
        logger.error(f"Unexpected error retrieving job {job_id}: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': { 'Content-Type': 'application/json' },
            'body': json.dumps({'error': 'An internal server error occurred'})
        }
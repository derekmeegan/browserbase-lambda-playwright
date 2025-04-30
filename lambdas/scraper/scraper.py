import os
import uuid
import json
import boto3
import asyncio
import logging
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from browserbase import Browserbase, BrowserbaseError
from playwright.async_api import async_playwright
from typing import Optional

# --- Logging Setup ---
logger = logging.getLogger()
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.setLevel(log_level)

# --- Configuration from Environment Variables ---
BROWSERBASE_API_KEY_SECRET_ARN = os.environ.get("BROWSERBASE_API_KEY_SECRET_ARN")
BROWSERBASE_PROJECT_ID_ARN = os.environ.get("BROWSERBASE_PROJECT_ID_ARN")
JOB_STATUS_TABLE_NAME = os.environ.get("JOB_STATUS_TABLE_NAME")

# --- AWS Clients ---
secrets_manager_client = boto3.client('secretsmanager')
dynamodb = boto3.resource('dynamodb')
job_table = dynamodb.Table(JOB_STATUS_TABLE_NAME)

# --- Secret Retrieval Function ---
def get_secret_value(secret_arn: str, expected_key: str) -> Optional[str]:
    """Retrieves a secret value from AWS Secrets Manager."""
    if not secret_arn:
        logger.error(f"Secret ARN for key '{expected_key}' is not provided.")
        return None
    logger.info(f"Attempting to retrieve secret with ARN: {secret_arn}")
    try:
        response = secrets_manager_client.get_secret_value(SecretId=secret_arn)
        if 'SecretString' in response:
            secret_data = json.loads(response['SecretString'])
            if expected_key in secret_data:
                value = secret_data[expected_key]
                logger.info(f"Successfully retrieved secret for key: {expected_key}")
                return value
            else:
                logger.error(f"Key '{expected_key}' not found in secret JSON for ARN: {secret_arn}")
                return None
        else:
            logger.error(f"SecretString not found in response for ARN: {secret_arn}")
            return None
    except (ClientError, json.JSONDecodeError, Exception) as e:
        logger.error(f"Error retrieving or parsing secret {secret_arn}: {e}", exc_info=True)
        return None

# --- DynamoDB Helper Function ---
def update_job_status(job_id: str, status: str, result_data: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None):
    """Updates the job status and results in DynamoDB."""
    if not job_table:
        logger.error("DynamoDB table not configured. Cannot update job status.")
        return

    timestamp = datetime.now(timezone.utc).isoformat()
    item = {
        'jobId': job_id,
        'status': status,
        'lastUpdatedAt': timestamp,
    }
    if result_data:
        item.update(result_data)
    if error_message:
        item['errorMessage'] = error_message

    try:
        logger.info(f"Updating DynamoDB for jobId {job_id} with status {status}")
        job_table.put_item(Item=item)
        logger.info(f"Successfully updated DynamoDB for jobId {job_id}")
    except ClientError as e:
        logger.error(f"Failed to update DynamoDB for jobId {job_id}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during DynamoDB update for jobId {job_id}: {e}", exc_info=True)

# --- Browserbase Session Creation (Modified for Free Tier) ---
def create_browserbase_session():
    """Creates a basic Browserbase session compatible with the free tier."""
    if not BROWSERBASE_PROJECT_ID_ARN:
        logger.error("BROWSERBASE_PROJECT_ID_ARN environment variable not set.")
        raise ValueError("BROWSERBASE_PROJECT_ID_ARN not set.")
    if not BROWSERBASE_API_KEY_SECRET_ARN:
        logger.error("BROWSERBASE_API_KEY_SECRET_ARN environment variable not set.")
        raise ValueError("BROWSERBASE_API_KEY_SECRET_ARN not set.")

    browserbase_api_key = get_secret_value(BROWSERBASE_API_KEY_SECRET_ARN, 'BROWSERBASE_API_KEY')
    browserbase_project_id = get_secret_value(BROWSERBASE_PROJECT_ID_ARN, 'BROWSERBASE_PROJECT_ID')

    if not browserbase_api_key or not browserbase_project_id:
        raise ValueError("Failed to retrieve Browserbase credentials from Secrets Manager.")

    bb = Browserbase(api_key=browserbase_api_key)

    session_args = {
        "project_id": browserbase_project_id,
    }
    logger.info(f"Attempting to create Browserbase session with args: {session_args}")

    try:
        session = bb.sessions.create(**session_args)
        logger.info(f"Session Created: {session.id}. URL: https://browserbase.com/sessions/{session.id}")
        return session
    except BrowserbaseError as e:
        logger.error(f"Error creating session: {e}")
        raise

# --- Scraper Function ---
async def scrape_page(payload: dict):
    """
    AWS Lambda handler function to run a simple Playwright task via Browserbase.
    """
    logger.info(f"Received event: {json.dumps(payload)}")
    job_id = payload.get("jobId", str(uuid.uuid4()))
    target_url = payload.get("url", "https://news.ycombinator.com/")

    initial_data = {
        'requestedUrl': target_url,
        'receivedAt': datetime.now(timezone.utc).isoformat()
    }
    update_job_status(job_id, "PENDING", result_data=initial_data)

    playwright = None
    browser = None
    session_id = None
    error_info = None
    final_status = "failed"
    results = {}

    try:
        # 1. Create Browserbase Session
        logger.info("Creating Browserbase session...")
        session = create_browserbase_session()
        connect_url = session.connect_url
        session_id = session.id
        initial_data['sessionId'] = session_id

        update_job_status(job_id, "RUNNING", result_data=initial_data)
        logger.info(f"Successfully created Browserbase session: {session_id}")

        # 2. Connect using Playwright
        logger.info(f"Attempting to connect to Browserbase session {session_id} via CDP...")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(connect_url, timeout=60000)
        logger.info("Connected to Browserbase session.")

        if not browser.contexts:
             logger.error("No browser contexts found in the connected session.")
             raise Exception("No browser contexts found.")
        context = browser.contexts[0]
        if not context.pages:
             logger.warning("No pages found in context, creating a new one.")
             page = await context.new_page()
        else:
             page = context.pages[0]
             logger.info("Using existing page from context.")

        # 3. Perform Simple Playwright Automation
        logger.info(f"Navigating to {target_url}...")

        await page.goto(target_url, wait_until="domcontentloaded", timeout=60000) # 60s navigation timeout
        page_title = await page.title()
        logger.info(f"Page title: {page_title}")
        content_length = len(await page.content())
        logger.info(f"Page content length: {content_length}")

        results = {
            'pageTitle': page_title,
            'contentLength': content_length,
        }
        final_status = "SUCCESS"
        logger.info("Playwright automation task completed successfully.")

    except BrowserbaseError as e:
        error_info = f"Browserbase API error: {e}"
        logger.error(error_info, exc_info=True)
    except TimeoutError as e:
        error_info = f"Playwright timeout error: {e}"
        logger.error(error_info, exc_info=True)
    except Exception as e:
        error_info = f"An unexpected error occurred: {e}"
        logger.error(error_info, exc_info=True)
    finally:
        # 4. Update DynamoDB
        final_data = initial_data.copy()
        final_data.update(results) 
        update_job_status(job_id, final_status, result_data=final_data, error_message=error_info)

        # 5. Cleanup
        if browser and browser.is_connected():
            logger.info("Closing browser connection...")
            await browser.close()
        if playwright:
            logger.info("Stopping Playwright...")
            await playwright.stop()

        logger.info(f"scrape_page finished for jobId: {job_id} with status: {final_status}")

    return {'jobId': job_id, 'finalStatus': final_status}

# --- Lambda Handler ---
def lambda_handler(event, context):
    """
    Handles API Gateway async invocation. Parses request, triggers scrape_page,
    and returns immediately (result handling is done via DynamoDB).
    """
    logger.info(f"Lambda handler invoked with event: {json.dumps(event)}")
    
    body = event.get('body')
    if not body:
        logger.error("Request body is missing or empty.")
        return {'status': 'error', 'message': 'Missing request body'}

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON body: {body}")
        return {'status': 'error', 'message': 'Invalid JSON body'}

    result = asyncio.run(scrape_page(payload))

    logger.info(f"Lambda handler completed for jobId: {result.get('jobId')}. Scraper status (for logs): {result.get('finalStatus')}")

    return {'status': 'accepted', 'jobId': result.get('jobId')}  

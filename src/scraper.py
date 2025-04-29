import os
import json
import boto3
import asyncio
import logging
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

# --- AWS Clients ---
secrets_manager_client = boto3.client('secretsmanager')

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
async def scrape_page(event):
    """
    AWS Lambda handler function to run a simple Playwright task via Browserbase.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    target_url = event.get("url", "https://news.ycombinator.com/")

    playwright = None
    browser = None
    page_title = None
    session_id = None
    status = "failed"

    try:
        # 1. Create Browserbase Session
        logger.info("Creating Browserbase session...")
        session = create_browserbase_session()
        connect_url = session.connect_url
        session_id = session.id
        logger.info(f"Successfully created Browserbase session: {session_id}")

        # 2. Connect using Playwright
        logger.info(f"Attempting to connect to Browserbase session {session_id} via CDP...")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(connect_url, timeout=60000)
        logger.info("Connected to Browserbase session.")

        if not browser.contexts:
             logger.error("No browser contexts found in the connected session.")
             raise Exception("No browser contexts found.")
        context = browser.contexts
        page = context.pages if context.pages else await context.new_page()
        logger.info(f"Using page (initial URL: {page.url})")

        # 3. Perform Simple Playwright Automation
        logger.info(f"Navigating to {target_url}...")

        await page.goto(target_url, wait_until="domcontentloaded", timeout=60000) # 60s navigation timeout
        page_title = await page.title()
        logger.info(f"Page title: {page_title}")
        content_length = len(await page.content())
        logger.info(f"Page content length: {content_length}")

        status = "success"
        logger.info("Playwright automation task completed successfully.")

    except BrowserbaseError as e:
        logger.error(f"Browserbase API error: {e}", exc_info=True)
        return {'status': 'failed', 'error': f"Browserbase API error: {e}", 'session_id': session_id}
    except TimeoutError as e:
         logger.error(f"Playwright timeout error: {e}", exc_info=True)
         return {'status': 'failed', 'error': f"Playwright timeout: {e}", 'session_id': session_id}
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return {'status': 'failed', 'error': f"Unexpected error: {e}", 'session_id': session_id}
    finally:
        # 4. Cleanup
        if browser and browser.is_connected():
            logger.info("Closing browser connection...")
            await browser.close()
        if playwright:
            logger.info("Stopping Playwright...")
            await playwright.stop()
        logger.info("Lambda execution finished.")

    return {
        'status': status,
        'session_id': session_id,
        'requested_url': target_url,
        'page_title': page_title,
        'content_length': content_length
    }

# --- Lambda Handler ---
def lambda_handler(event, context):
    return asyncio.run(scrape_page(event))

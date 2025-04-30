import requests
import json
import uuid
import time
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
API_ENDPOINT_URL = os.getenv("API_ENDPOINT_URL")
API_KEY = os.getenv("API_KEY")

# Default URL to scrape if not provided otherwise
DEFAULT_URL_TO_SCRAPE = "https://news.ycombinator.com/"

# Polling configuration
POLL_INTERVAL_SECONDS = 2
MAX_POLL_ATTEMPTS = 50

# --- Helper Functions ---
def submit_job(job_id: str, url: str, endpoint_url: str, api_key: str) -> bool:
    """Submits a new scrape job to the API."""
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key
    }
    payload = {
        'jobId': job_id,
        'url': url
    }
    print(f"Submitting job {job_id} for URL: {url}...")
    try:
        response = requests.post(endpoint_url, headers=headers, json=payload)
        response.raise_for_status()

        if response.status_code == 202:
            print(f"Job {job_id} accepted successfully (Status Code: {response.status_code}).")
            return True
        else:
            print(f"Unexpected success status code: {response.status_code}")
            print(f"Response body: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error submitting job {job_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return False

def get_job_status(job_id: str, endpoint_url_base: str, api_key: str) -> dict | None:
    """Polls the API to get the status and results of a job."""
    endpoint = f"{endpoint_url_base}/{job_id}"
    headers = {
        'x-api-key': api_key
    }
    status_check_timeout = 20

    print(f"Checking status for job {job_id}...")
    try:
        response = requests.get(endpoint, headers=headers, timeout=status_check_timeout)
        response.raise_for_status()

        if response.status_code == 200:
            return response.json()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Job {job_id} not found yet (Status 404). Might still be processing.")
            return None # Job might not have been processed yet or ID is wrong
        else:
            print(f"HTTP error getting status for job {job_id}: {e}")
            print(f"Response body: {e.response.text}")
            return {"status": "ERROR_CHECKING", "error": str(e)} # Indicate error checking status
    except requests.exceptions.Timeout:
        print(f"Timeout waiting for status response for job {job_id}.")
        return None # Indicate timeout, can retry
    except requests.exceptions.RequestException as e:
        print(f"Network error getting status for job {job_id}: {e}")
        return {"status": "ERROR_CHECKING", "error": str(e)}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response for job {job_id}: {e}")
        return {"status": "ERROR_CHECKING", "error": f"Invalid JSON response: {e}"}

def main(url: str = None):
    """Main execution logic."""
    if not API_ENDPOINT_URL or not API_KEY:
        print("Error: Environment variables API_ENDPOINT_URL and API_KEY must be set.")
        print("Please export them before running the script:")
        print("  export API_ENDPOINT_URL='https://your-api-id.execute-api.your-region.amazonaws.com/v1/scrape'")
        print("  export API_KEY='your-actual-api-key-value'")
        sys.exit(1)

    if url is None:
        url = DEFAULT_URL_TO_SCRAPE

    # 1. Generate a unique Job ID
    job_id = str(uuid.uuid4())
    print(f"Generated Job ID: {job_id}")

    # 2. Submit the job
    if submit_job(job_id, url, API_ENDPOINT_URL, API_KEY):
        # 3. Poll for results
        print(f"\nPolling for job completion every {POLL_INTERVAL_SECONDS} seconds...")
        attempts = 0
        final_result = None
        while attempts < MAX_POLL_ATTEMPTS:
            attempts += 1
            # Wait *before* polling (except the first time)
            if attempts > 1:
                 time.sleep(POLL_INTERVAL_SECONDS)

            result = get_job_status(job_id, API_ENDPOINT_URL, API_KEY)

            if result:
                status = result.get('status', 'UNKNOWN')
                print(f"Polling attempt {attempts}/{MAX_POLL_ATTEMPTS}: Status = {status}")
                if status in ["SUCCESS", "FAILED", "ERROR_CHECKING"]:
                    final_result = result
                    break
            else:
                print(f"Polling attempt {attempts}/{MAX_POLL_ATTEMPTS}: No status update yet or check failed.")

        # 4. Print final result
        print("\n--- Final Result ---")
        if final_result:
            print(json.dumps(final_result, indent=2))
            final_status = final_result.get('status')
            if final_status == 'FAILED':
                print("\nJob failed.")
            elif final_status == 'SUCCESS':
                print("\nJob completed successfully.")
            else: # Handle ERROR_CHECKING or UNKNOWN
                print(f"\nJob polling finished with status: {final_status}")
        else:
            print(f"Job {job_id} did not reach a final state (SUCCESS/FAILED) within the polling time limit ({MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS} seconds).")
            print("It might still be running or encountered an issue. Check status manually later:")
            print(f"  curl -H \"x-api-key: {API_KEY}\" {API_ENDPOINT_URL}/{job_id}")


if __name__ == "__main__":
    url = None
    main(url)

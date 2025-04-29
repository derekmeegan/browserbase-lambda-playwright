# Browserbase Lambda Playwright

A serverless web agent and automation framework that combines AWS Lambda, Docker, and Browserbase to run Playwright-powered web agents and browser automation tasks without the complexity of managing browser dependencies within Lambda. Perfect for building autonomous web agents, scrapers, and automated workflows in a serverless environment.

## Overview

This project provides a complete infrastructure for deploying a Playwright-based web automation solution using:

- **AWS Lambda** with Docker container deployment
- **Browserbase** for remote browser execution
- **AWS CDK** for infrastructure as code
- **GitHub Actions** for CI/CD

## Key Advantages

- **No Lambda Layers Required**: Package Playwright and all dependencies in a Docker container
- **Low Lambda Resource Consumption**: Offload browser execution to Browserbase
- **Durability & Offloaded State Management**: Browserbase sessions manage browser state
- **Simplified Dependencies**: Minimal Python dependencies (playwright, browserbase, boto3)
- **Built-in CI/CD Pipeline**: GitHub Actions workflow for automated deployment
- **Scalability Focus Shift**: Scale by adjusting Browserbase plan rather than complex Lambda configurations

## Prerequisites

- AWS Account
- Browserbase Account
- Docker installed locally
- AWS CLI installed
- Node.js and npm installed (for AWS CDK)
- Python 3.12+ installed

## Setup Instructions

### 1. Install AWS CLI

#### macOS
```bash
brew install awscli
```

#### Windows
Download and run the installer from: https://aws.amazon.com/cli/

#### Linux
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 2. Configure AWS CLI

```bash
aws configure
```

You'll need to provide:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Default output format (json recommended)

### 3. Getting AWS Access Keys

1. Log in to the AWS Management Console
2. Navigate to IAM (Identity and Access Management)
3. Click on "Users" in the left navigation pane
4. Click on your username or create a new user
5. Select the "Security credentials" tab
6. Under "Access keys", click "Create access key"
7. Download the CSV file or copy the Access Key ID and Secret Access Key

**Note**: For production use, follow AWS best practices by creating a user with only the necessary permissions.

### 4. Sign up for Browserbase

1. Visit [Browserbase](https://browserbase.com/) and sign up for an account
2. After signing up, navigate to your dashboard
3. Create a new project or use the default project
4. Note your API key and Project ID from the dashboard

### 5. Create AWS Secrets for Browserbase Credentials

Create secrets for your Browserbase API key and Project ID:

```bash
# Create secret for Browserbase API Key
aws secretsmanager create-secret \
    --name BrowserbaseLambda/BrowserbaseApiKey \
    --secret-string '{"BROWSERBASE_API_KEY":"your-api-key-here"}'

# Create secret for Browserbase Project ID
aws secretsmanager create-secret \
    --name BrowserbaseLambda/BrowserbaseProjectId \
    --secret-string '{"BROWSERBASE_PROJECT_ID":"your-project-id-here"}'
```

### 6. Install Playwright Locally (for Development)

```bash
# Install Playwright
pip install playwright

# Install browser binaries
python -m playwright install
```

## Project Structure

```
browserbase-lambda-playwright/
├── .github/workflows/      # GitHub Actions workflows
│   └── deploy.yaml         # CI/CD pipeline for deployment
├── infra/                  # AWS CDK infrastructure code
│   ├── app.py              # CDK app entry point
│   ├── stack.py            # CDK stack definition
│   ├── cdk.json            # CDK configuration
│   └── requirements.txt    # Python dependencies for CDK
├── src/                    # Lambda function source code
│   ├── scraper.py          # Main Lambda handler
│   ├── Dockerfile          # Docker container definition
│   └── requirements.txt    # Python dependencies for Lambda
└── README.md               # Project documentation
```

## Deployment

### Manual Deployment

```bash
# Install CDK dependencies
cd infra
pip install -r requirements.txt

# Deploy the stack
cdk deploy
```

### Automated Deployment via GitHub Actions

The project includes a GitHub Actions workflow that automatically deploys the infrastructure when changes are pushed to the main branch.

To use this workflow:

1. Clone this repository to your GitHub account:
   ```bash
   git clone https://github.com/yourusername/browserbase-lambda-playwright.git
   cd browserbase-lambda-playwright
   ```

2. Add the following secrets to your GitHub repository:
   - `AWS_ACCESS_KEY`: Your AWS Access Key ID
   - `AWS_SECRET_ACCESS_KEY`: Your AWS Secret Access Key

3. Push changes to the main branch to trigger deployment

## Free vs. Paid Browserbase Capabilities

This project is designed to work with Browserbase's free tier, which is suitable for development and testing but has limitations:

### Free Tier Limitations

- **Concurrency**: Limited to 1 concurrent browser session
- **Rate Limit**: Limited to creating 1 new session per minute
- **Proxies**: Not supported (0GB allowance)
- **Fingerprinting/Stealth**: Not available
- **Keep-Alive**: Not available
- **Browser Hours**: Limited usage (e.g., 1 hour/month)

## Use Cases Beyond Scraping

While this architecture is well-suited for standard browser automation tasks like web scraping and data extraction, it can be extended to build serverless web agents for:

- Monitoring websites for changes and triggering actions
- Performing complex sequences of actions across multiple web pages
- Providing a "browser tool" for Large Language Models (LLMs)
- Automating repetitive user interactions within web applications

## License

MIT

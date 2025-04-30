# 🚀 Serverless Browser Agents with Playwright + Lambda + Browserbase
*Spin up headless browsers on AWS in under a minute—no layers, no EC2, no pain.*

[![Build](https://github.com/derekmeegan/browserbase-lambda-playwright/actions/workflows/deploy.yaml/badge.svg)](../../actions/workflows/deploy.yaml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Star ⭐ this repo if it saves you hours, and hit _Fork_ to make it yours in seconds.**

---

## ⚡ TL;DR Quick-Start

### Option A: Local Deployment

```bash
# 1. Clone this repository
git clone https://github.com/your-username/browserbase-lambda-playwright.git
cd browserbase-lambda-playwright

# 2. Deploy infrastructure
env | grep AWS || export AWS_ACCESS_KEY_ID=... && export AWS_SECRET_ACCESS_KEY=...
cd infra && pip install -r requirements.txt && cdk deploy --all --require-approval never

# 3. Fetch API details from CloudFormation outputs
echo "export API_ENDPOINT_URL=$(aws cloudformation describe-stacks \
  --stack-name BrowserbaseLambdaStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpointUrl`].OutputValue' \
  --output text)"

echo "export API_KEY=$(aws apigateway get-api-key \
  --api-key $(aws cloudformation describe-stacks --stack-name BrowserbaseLambdaStack \
      --query 'Stacks[0].Outputs[?OutputKey==`ApiKeyId`].OutputValue' --output text) \
  --include-value \
  --query 'value' \
  --output text)"

# 4. Install example dependencies and run quick start
pip install -r examples/requirements.txt
python examples/quick_start.py
```

### Option B: GitHub Actions Deployment

```bash
# 1. Fork or push this repo to your GitHub account
# 2. Add repository secrets under Settings → Secrets & variables → Actions:
#    - AWS_ACCESS_KEY
#    - AWS_SECRET_ACCESS_KEY
# 3. Create Browserbase secrets in AWS Secrets Manager (see infra/stack.py env names)
# 4. Push to main → GitHub Actions triggers CDK deploy
```

You now have a Lambda that opens a Browserbase session and runs Playwright code from **`lambdas/scraper/scraper.py`**.  
Invoke it with:

```bash
curl -X POST "$API_ENDPOINT_URL" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"url":"https://news.ycombinator.com/"}' \
  -v

# …then poll status:
curl -H "x-api-key: $API_KEY" "$API_ENDPOINT_URL/<jobId>"
```

---

## 🔄 Serverless Async Architecture

1. **POST /scrape** returns **202 Accepted** immediately.  
2. Job metadata is stored in DynamoDB (`JobStatusTable`) with status updates (PENDING → RUNNING → SUCCESS/FAILED).  
3. **GET /scrape/{jobId}** polls DynamoDB for the latest job result.  

---

## 🚀 Why use this template?

* **Zero binary juggling** – Playwright lives in the Lambda image; Chrome runs remotely on Browserbase.  
* **Cold-start ≈ 2 s** – no browser download, just connect-over-CDP.  
* **Pay-per-run** – pure Lambda pricing; scale by upgrading Browserbase, not infra.  
* **Async, serverless** – fire-and-forget POST, durable job tracking via DynamoDB.  
* **Built-in CI/CD** – GitHub Actions deploys on every push to `main`/`staging`.

---

## 🏗️ High-Level Architecture

```text
     ┌────────────┐  CDP (WebSocket)  ┌────────────┐
     │ AWS Lambda │ ────────────────▶ │ Browserbase│
     └────────────┘                   └────────────┘
           │              Logs
           ▼
     AWS CloudWatch
           │
           ▼
     Amazon DynamoDB (JobStatusTable)
```  

---

## 📦 Project Layout

```
.
├── .github/workflows/deploy.yaml
├── examples/
│   ├── quick_start.py
│   └── requirements.txt
├── infra/
│   ├── app.py
│   ├── cdk.json
│   ├── requirements.txt
│   └── stack.py
├── lambdas/
│   ├── getter/
│   │   ├── Dockerfile
│   │   ├── getter.py
│   │   └── requirements.txt
│   └── scraper/
│       ├── Dockerfile
│       ├── scraper.py
│       └── requirements.txt
├── .gitignore
├── README.md
└── LICENSE
```

---

<details>
<summary>🔍 Full Setup & Prerequisites</summary>

### Requirements

| Tool                      | Version      |
| ------------------------- | ------------ |
| AWS CLI                   | any 2.x      |
| Docker                    | ≥ 20.10      |
| Node & npm                | any LTS      |
| Python                    | 3.12+        |
| Browserbase account       | free tier OK |

### 1. Install the AWS CLI

```bash
# macOS (Homebrew)
brew install awscli
```

(See AWS docs for Windows/Linux.)

### 2. Configure AWS

```bash
aws configure  # supply keys & default region, e.g. us-east-1
```

### 3. Add Browserbase secrets to AWS Secrets Manager

```bash
aws secretsmanager create-secret \
  --name BrowserbaseLambda/BrowserbaseApiKey \
  --secret-string '{"BROWSERBASE_API_KEY":"$BROWSERBASE_API_KEY"}'

aws secretsmanager create-secret \
  --name BrowserbaseLambda/BrowserbaseProjectId \
  --secret-string '{"BROWSERBASE_PROJECT_ID":"$BROWSERBASE_PROJECT_ID"}'
```

### 4. (Optional) Local Playwright install

```bash
pip install playwright && python -m playwright install
```

</details>

---

## ❓ FAQ

| Question                                          | Answer                                                                              |
| ------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **Browserbase free tier?**                        | Yes—1 concurrent session; creation rate‑limited.                                     |
| **Cold‑starts?**                                  | Typical < 2 s (CDP connect, no browser download).                                    |
| **Add extra Python libs?**                        | Add to `lambdas/<getter|scraper>/requirements.txt`, rebuild images, push → redeploy. |
| **API returns 202 Accepted—how to track status?** | Poll `GET /scrape/{jobId}` to read status/results from DynamoDB.                     |

---

## 🤝 Contributing

Pull requests are welcome! Please open an issue first if you plan a large change.

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.


# 🚀 Serverless Browser Agents with Playwright + Lambda + Browserbase
*Spin up headless browsers on AWS in under a minute—no layers, no EC2, no pain.*

[![Build](https://github.com/derekmeegan/browserbase-lambda-playwright/actions/workflows/deploy.yaml/badge.svg)](../../actions/workflows/deploy.yaml)  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Star ⭐ this repo if it saves you hours, and hit _Fork_ to make it yours in seconds.**

---

## ⚡ TL;DR Quick-Start

### Option A: Local Deployment

```bash
# 1. Clone this repository
git clone https://github.com/your-username/browserbase-lambda-playwright.git
cd browserbase-lambda-playwright

# 2. Deploy infrastructure
env | grep AWS || export AWS_ACCESS_KEY_ID=... && export AWS_SECRET_ACCESS_KEY=...
cd infra && pip install -r requirements.txt && cdk deploy --all --require-approval never

# 3. Fetch API details from CloudFormation outputs
echo "export API_ENDPOINT_URL=$(aws cloudformation describe-stacks \
  --stack-name BrowserbaseLambdaStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpointUrl`].OutputValue' \
  --output text)"

echo "export API_KEY=$(aws apigateway get-api-key \
  --api-key $(aws cloudformation describe-stacks --stack-name BrowserbaseLambdaStack \
      --query 'Stacks[0].Outputs[?OutputKey==`ApiKeyId`].OutputValue' --output text) \
  --include-value \
  --query 'value' \
  --output text)"

# 4. Install example dependencies and run quick start
pip install -r examples/requirements.txt
python examples/quick_start.py
```

### Option B: GitHub Actions Deployment

```bash
# 1. Fork or push this repo to your GitHub account
# 2. Add repository secrets under Settings → Secrets & variables → Actions:
#    - AWS_ACCESS_KEY
#    - AWS_SECRET_ACCESS_KEY
# 3. Create Browserbase secrets in AWS Secrets Manager (see infra/stack.py env names)
# 4. Push to main → GitHub Actions triggers CDK deploy
```

---

## 🔄 Serverless Async Architecture

1. **POST /scrape** returns **202 Accepted** immediately.  
2. Job metadata is stored in DynamoDB (`JobStatusTable`) with status updates (PENDING → RUNNING → SUCCESS/FAILED).  
3. **GET /scrape/{jobId}** polls DynamoDB for the latest job result.  

---

## 🚀 Why use this template?

* **Zero binary juggling** – Playwright lives in the Lambda image; Chrome runs remotely on Browserbase.  
* **Cold-start ≈ 2 s** – no browser download, just connect-over-CDP.  
* **Pay-per-run** – pure Lambda pricing; scale by upgrading Browserbase, not infra.  
* **Async, serverless** – fire-and-forget POST, durable job tracking via DynamoDB.  
* **Built-in CI/CD** – GitHub Actions deploys on every push to `main`/`staging`.

---

## 🏗️ High-Level Architecture

```text
     ┌────────────┐  CDP (WebSocket)  ┌────────────┐
     │ AWS Lambda │ ────────────────▶ │ Browserbase│
     └────────────┘                   └────────────┘
           │              Logs
           ▼
     AWS CloudWatch
           │
           ▼
     Amazon DynamoDB (JobStatusTable)
```  

---

## 📦 Project Layout

```text
.
├── .github/workflows/deploy.yaml   # CI/CD pipeline
├── examples/                      # Example usage
│   ├── quick_start.py
│   └── requirements.txt
├── infra/                         # CDK IaC
│   ├── app.py
│   ├── cdk.json
│   ├── requirements.txt
│   └── stack.py
├── lambdas/                       # Lambda handlers
│   ├── getter/
│   │   ├── Dockerfile
│   │   ├── getter.py
   │   └── requirements.txt
│   └── scraper/
│       ├── Dockerfile
│       ├── scraper.py
│       └── requirements.txt
├── .gitignore
├── README.md
└── LICENSE
```

---

<details>
<summary>🔍 Full Setup & Prerequisites</summary>

### Requirements

| Tool                      | Version      |
| ------------------------- | ------------ |
| AWS CLI                   | any 2.x      |
| Docker                    | ≥ 20.10      |
| Node & npm                | any LTS      |
| Python                    | 3.12+        |
| Browserbase account       | free tier OK |

### 1. Install AWS CLI

```bash
brew install awscli   # macOS via Homebrew
```  
(See AWS docs for Windows/Linux.)

### 2. Configure AWS

```bash
aws configure  # keys & default region (e.g. us-east-1)
```

### 3. Create Browserbase Secrets

```bash
aws secretsmanager create-secret \
  --name BrowserbaseLambda/BrowserbaseApiKey \
  --secret-string '{"BROWSERBASE_API_KEY":"$BROWSERBASE_API_KEY"}'

aws secretsmanager create-secret \
  --name BrowserbaseLambda/BrowserbaseProjectId \
  --secret-string '{"BROWSERBASE_PROJECT_ID":"$BROWSERBASE_PROJECT_ID"}'
```

### 4. (Optional) Local Playwright install

```bash
pip install playwright && python -m playwright install
```

</details>

---

## ❓ FAQ

| Question                                          | Answer                                                                              |
| ------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **Browserbase free tier?**                        | Yes—1 concurrent session; creation rate‑limited.                                     |
| **Cold‑starts?**                                  | Typical < 2 s (CDP connect, no browser download).                                    |
| **Add extra Python libs?**                        | Add to `lambdas/<getter|scraper>/requirements.txt`, rebuild images, push → redeploy. |
| **API returns 202 Accepted—how to track status?** | Poll `GET /scrape/{jobId}` to read status/results from DynamoDB.                     |

---

## 🤝 Contributing

Pull requests welcome! Please open an issue for major changes.

---

## 📄 License

This project is licensed under the MIT License – see [LICENSE](LICENSE) for details.


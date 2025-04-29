# 🚀 Serverless Browser Agents with Playwright + Lambda + Browserbase
*Spin up headless browsers on AWS in under a minute—no layers, no EC2, no pain.*

[![Build](https://github.com/your-username/your-repo/actions/workflows/deploy.yaml/badge.svg)](../../actions/workflows/deploy.yaml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Star ⭐ this repo if it saves you hours, and hit _Fork_ to make it yours in seconds.**

---

## ⚡ TL;DR Quick-Start

### Option A: Local Deployment

```bash
# 1. Clone this repository
git clone https://github.com/your-username/browserbase-lambda-playwright.git
cd browserbase-lambda-playwright

# 2. Export AWS & Browserbase secrets
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export BROWSERBASE_API_KEY=...
export BROWSERBASE_PROJECT_ID=...

# 3. Create AWS Secrets Manager entries
aws secretsmanager create-secret \
  --name BrowserbaseLambda/BrowserbaseApiKey \
  --secret-string '{"BROWSERBASE_API_KEY":"'"$BROWSERBASE_API_KEY"'"}'

aws secretsmanager create-secret \
  --name BrowserbaseLambda/BrowserbaseProjectId \
  --secret-string '{"BROWSERBASE_PROJECT_ID":"'"$BROWSERBASE_PROJECT_ID"'"}'

# 4. Deploy (creates the Lambda + IAM + Secrets wiring)
cd infra && pip install -r requirements.txt && cdk deploy --all --require-approval never
```

### Option B: GitHub Actions Deployment

```bash
# 1. Create your own repository
# Either fork this repository on GitHub or create a new one and push this code

# 2. Add GitHub repository secrets
# Go to your repository → Settings → Secrets and variables → Actions → New repository secret
# Add these secrets:
# - AWS_ACCESS_KEY: Your AWS Access Key ID
# - AWS_SECRET_ACCESS_KEY: Your AWS Secret Access Key

# 3. Create AWS Secrets Manager entries (same as Option A step 3)

# 4. Push to main branch to trigger deployment
git push origin main
```

You now have a Lambda that opens a Browserbase session and runs Playwright code from **`src/scraper.py`**.  
Invoke it with:

```bash
aws lambda invoke \
  --function-name <deployed-lambda-name> \
  --payload '{"url":"https://news.ycombinator.com/"}' \
  response.json && cat response.json | jq
```

---

## 🚀 Why use this template?

* **Zero binary juggling** – Playwright lives in the Docker image; heavy Chrome lives on Browserbase.  
* **Cold-start ≈ 2 s** – no browser download, just connect-over-CDP.  
* **Pay-per-run** – pure Lambda pricing; scale by upgrading Browserbase, not infra.  
* **Built-in CI/CD** – GitHub Actions deploys on every push to `main`.  

---

## 🏗️ High-Level Architecture

```
     ┌────────────┐  CDP (WebSocket)  ┌────────────┐
     │ AWS Lambda │ ────────────────▶ │ Browserbase│
     └────────────┘                   └────────────┘
           │              Logs
           ▼
     AWS CloudWatch
```

---

## 📦 Project Layout

```
.
├── .github/workflows/deploy.yaml   # CI/CD pipeline
├── infra/                          # CDK IaC
│   ├── app.py
│   ├── stack.py
│   └── requirements.txt
└── src/
    ├── Dockerfile                  # Lambda image
    ├── scraper.py                  # Playwright logic
    └── requirements.txt
```

---

<details>
<summary>🔍 Full Setup & Prerequisites</summary>

### Requirements

| Tool | Version |
| --- | --- |
| AWS CLI | any 2.x |
| Docker | ≥ 20.10 |
| Node & npm | any LTS (for CDK) |
| Python | 3.12+ |
| Browserbase account | free tier works |

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

### 4. Local Playwright install (optional for dev)

```bash
pip install playwright && python -m playwright install
```

</details>

---

## ❓ FAQ

| Question | Answer |
| --- | --- |
| **Does this work on Browserbase free tier?** | Yes—1 concurrent session and rate-limited creation. |
| **Cold-starts?** | Typical < 2000 ms; browser runs remotely. |
| **How do I add extra Python libs?** | Add them to `src/requirements.txt`, rebuild, push—GitHub Actions redeploys. |

---

## 🤝 Contributing

Pull requests are welcome! Please open an issue first if you plan a large change.

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
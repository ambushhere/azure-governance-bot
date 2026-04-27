# 🌱 Azure Governance Bot
<img width="2048" height="2048" alt="Gemini_Generated_Image_6spy9f6spy9f6spy" src="https://github.com/user-attachments/assets/34227b20-7f3b-4a80-bba2-b3eaa39d3cdb" />

[![Azure](https://img.shields.io/badge/Provider-Azure-blue.svg)](https://azure.microsoft.com/)
[![Python](https://img.shields.io/badge/Language-Python-green.svg)](https://www.python.org/)
[![CI](https://github.com/ambushhere/azure-governance-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/ambushhere/azure-governance-bot/actions/workflows/ci.yml)

An automated tool for auditing resources in Microsoft Azure.

### 🚀 Key Features
- **Tag Auditing**: Validates `CostCenter`, `Owner`, and `Environment` tags across all resource groups.
- **CI/CD Ready**: Lint & test pipeline via GitHub Actions (no Azure subscription required).
- **FinOps Focused**: Identifies unused resources to reduce cloud spend (preview).

📈 Result / Impact

• Improved governance quality by validating required tags (CostCenter, Owner, Environment) across resource groups.
• Increased reliability with automated CI checks (tests + lint) on each push/PR.
• Added stricter compliance logic to detect empty/whitespace tag values (not only missing keys).
• Hardened runtime behavior by returning non-zero exit code on startup/config errors, making failures visible in automation pipelines.

### 📋 Setup

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Or install with dev/test dependencies
pip install -r requirements-dev.txt
```

### ▶️ Usage

```bash
# Authenticate with Azure
az login
export AZURE_SUBSCRIPTION_ID="<your-subscription-id>"

# Run the bot
python azure_governance_bot.py
```

### 🧪 Testing

All tests mock the Azure SDK, so **no Azure subscription is needed** to run them:

```bash
pytest tests/ -v
```

### 🔍 Linting

```bash
flake8 azure_governance_bot.py tests/
```

### 📂 Project Structure

```
├── azure_governance_bot.py   # Main bot logic
├── tests/
│   └── test_azure_governance_bot.py  # Unit tests (mocked Azure SDK)
├── .github/workflows/
│   └── ci.yml                # GitHub Actions CI pipeline
├── requirements.txt          # Runtime dependencies
├── requirements-dev.txt      # Dev/test dependencies
└── README.md
```


# 🌱 Azure Governance Bot

[![Azure](https://img.shields.io/badge/Provider-Azure-blue.svg)](https://azure.microsoft.com/)
[![Python](https://img.shields.io/badge/Language-Python-green.svg)](https://www.python.org/)

An automated tool for auditing resources in Microsoft Azure.

### 🚀 Key Features
- **Tag Auditing**: Validates `CostCenter`, `Owner`, and `Environment` tags.
- **CI/CD Ready**: Fully automated via GitHub Actions.
- **FinOps Focused**: Identifies unused resources to reduce cloud spend.

### 📋 Setup
1. `pip install -r requirements.txt`
2. `az login`
3. `python azure_governance_bot.py`

"""Unit tests for AzureGovernanceBot.

All Azure SDK calls are mocked so the tests run without an Azure
subscription or any network access.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from azure_governance_bot import AuditResult, AzureGovernanceBot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rg(name: str, tags: dict | None = None) -> SimpleNamespace:
    """Return a lightweight object that looks like a ResourceGroup."""
    return SimpleNamespace(name=name, tags=tags)


# ---------------------------------------------------------------------------
# AuditResult
# ---------------------------------------------------------------------------

class TestAuditResult:
    def test_empty_result(self):
        r = AuditResult()
        assert r.compliant_count == 0
        assert r.non_compliant_count == 0

    def test_counts(self):
        r = AuditResult(
            compliant=["rg-ok"],
            non_compliant={"rg-bad": ["Owner"]},
        )
        assert r.compliant_count == 1
        assert r.non_compliant_count == 1


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------

class TestInit:
    @patch("azure_governance_bot.ResourceManagementClient")
    @patch("azure_governance_bot.DefaultAzureCredential")
    def test_subscription_from_arg(self, _cred, _client):
        bot = AzureGovernanceBot(subscription_id="test-sub-id")
        assert bot.subscription_id == "test-sub-id"

    @patch("azure_governance_bot.ResourceManagementClient")
    @patch("azure_governance_bot.DefaultAzureCredential")
    def test_subscription_from_env(self, _cred, _client, monkeypatch):
        monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "env-sub-id")
        bot = AzureGovernanceBot()
        assert bot.subscription_id == "env-sub-id"

    @patch("azure_governance_bot.ResourceManagementClient")
    @patch("azure_governance_bot.DefaultAzureCredential")
    def test_missing_subscription_raises(self, _cred, _client, monkeypatch):
        monkeypatch.delenv("AZURE_SUBSCRIPTION_ID", raising=False)
        with pytest.raises(ValueError, match="AZURE_SUBSCRIPTION_ID"):
            AzureGovernanceBot()


# ---------------------------------------------------------------------------
# audit_tags
# ---------------------------------------------------------------------------

class TestAuditTags:
    @patch("azure_governance_bot.ResourceManagementClient")
    @patch("azure_governance_bot.DefaultAzureCredential")
    def test_all_compliant(self, _cred, mock_client_cls):
        mock_client = MagicMock()
        mock_client.resource_groups.list.return_value = [
            _make_rg("rg-prod", {
                "CostCenter": "123",
                "Owner": "alice",
                "Environment": "prod",
            }),
        ]
        mock_client_cls.return_value = mock_client

        bot = AzureGovernanceBot(subscription_id="sub")
        result = bot.audit_tags()

        assert result.compliant == ["rg-prod"]
        assert result.non_compliant == {}

    @patch("azure_governance_bot.ResourceManagementClient")
    @patch("azure_governance_bot.DefaultAzureCredential")
    def test_non_compliant_missing_tags(self, _cred, mock_client_cls):
        mock_client = MagicMock()
        mock_client.resource_groups.list.return_value = [
            _make_rg("rg-dev", {"Owner": "bob"}),
        ]
        mock_client_cls.return_value = mock_client

        bot = AzureGovernanceBot(subscription_id="sub")
        result = bot.audit_tags()

        assert "rg-dev" in result.non_compliant
        assert "CostCenter" in result.non_compliant["rg-dev"]
        assert "Environment" in result.non_compliant["rg-dev"]

    @patch("azure_governance_bot.ResourceManagementClient")
    @patch("azure_governance_bot.DefaultAzureCredential")
    def test_no_tags_at_all(self, _cred, mock_client_cls):
        mock_client = MagicMock()
        mock_client.resource_groups.list.return_value = [
            _make_rg("rg-empty", None),
        ]
        mock_client_cls.return_value = mock_client

        bot = AzureGovernanceBot(subscription_id="sub")
        result = bot.audit_tags()

        assert result.non_compliant_count == 1
        assert sorted(result.non_compliant["rg-empty"]) == [
            "CostCenter",
            "Environment",
            "Owner",
        ]

    @patch("azure_governance_bot.ResourceManagementClient")
    @patch("azure_governance_bot.DefaultAzureCredential")
    def test_custom_mandatory_tags(self, _cred, mock_client_cls):
        mock_client = MagicMock()
        mock_client.resource_groups.list.return_value = [
            _make_rg("rg-a", {"Team": "platform"}),
        ]
        mock_client_cls.return_value = mock_client

        bot = AzureGovernanceBot(subscription_id="sub")
        result = bot.audit_tags(mandatory_tags=["Team"])

        assert result.compliant == ["rg-a"]

    @patch("azure_governance_bot.ResourceManagementClient")
    @patch("azure_governance_bot.DefaultAzureCredential")
    def test_mixed_compliance(self, _cred, mock_client_cls):
        mock_client = MagicMock()
        mock_client.resource_groups.list.return_value = [
            _make_rg("rg-ok", {
                "CostCenter": "1",
                "Owner": "a",
                "Environment": "p",
            }),
            _make_rg("rg-bad", {"Owner": "b"}),
        ]
        mock_client_cls.return_value = mock_client

        bot = AzureGovernanceBot(subscription_id="sub")
        result = bot.audit_tags()

        assert result.compliant_count == 1
        assert result.non_compliant_count == 1

    @patch("azure_governance_bot.ResourceManagementClient")
    @patch("azure_governance_bot.DefaultAzureCredential")
    def test_api_error_is_raised(self, _cred, mock_client_cls):
        mock_client = MagicMock()
        mock_client.resource_groups.list.side_effect = RuntimeError("boom")
        mock_client_cls.return_value = mock_client

        bot = AzureGovernanceBot(subscription_id="sub")
        with pytest.raises(RuntimeError, match="boom"):
            bot.audit_tags()

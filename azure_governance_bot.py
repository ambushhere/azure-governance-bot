import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient

# Professional logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("AzureGovernanceBot")

DEFAULT_MANDATORY_TAGS: List[str] = ["CostCenter", "Owner", "Environment"]


@dataclass
class AuditResult:
    """Result of a tag compliance audit."""

    compliant: List[str] = field(default_factory=list)
    non_compliant: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def compliant_count(self) -> int:
        return len(self.compliant)

    @property
    def non_compliant_count(self) -> int:
        return len(self.non_compliant)


class AzureGovernanceBot:
    """
    Automates resource auditing in Microsoft Azure.
    Helps maintain tagging compliance and optimize costs.

    Required Azure RBAC role: Reader (at subscription scope).
    Do NOT assign Contributor or higher — this bot is read-only.

    Required environment variables:
        AZURE_SUBSCRIPTION_ID — the target Azure subscription ID.

    Authentication is handled via DefaultAzureCredential, which supports:
        - Managed Identity (recommended for production)
        - Azure CLI (for local development)
        - Environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)
    """

    def __init__(self, subscription_id: Optional[str] = None):
        _sub_id = subscription_id or os.getenv("AZURE_SUBSCRIPTION_ID")
        if not _sub_id:
            raise ValueError(
                "AZURE_SUBSCRIPTION_ID must be set as an environment variable "
                "or passed to the constructor."
            )
        # Explicitly typed as str (not Optional) after validation
        self.subscription_id: str = _sub_id

        self.credential = DefaultAzureCredential()
        self.client = ResourceManagementClient(
            self.credential,
            self.subscription_id,
        )

    def audit_tags(
        self, mandatory_tags: Optional[List[str]] = None
    ) -> AuditResult:
        """Checks all resource groups for tagging policy compliance.

        Args:
            mandatory_tags: Tags that every resource group must have.
                Defaults to ``DEFAULT_MANDATORY_TAGS``.

        Returns:
            An ``AuditResult`` with compliant and non-compliant groups.
        """
        if mandatory_tags is None:
            mandatory_tags = list(DEFAULT_MANDATORY_TAGS)

        # FIX: mask subscription_id in logs to avoid leaking it to log aggregators
        masked_id = "***" + self.subscription_id[-4:]
        logger.info(
            "--- Starting tag audit for subscription: %s ---",
            masked_id,
        )
        result = AuditResult()

        try:
            resource_groups = self.client.resource_groups.list()

            for rg in resource_groups:
                tags = rg.tags or {}
                missing_tags = [
                    t
                    for t in mandatory_tags
                    if tags.get(t) is None
                    or (
                        isinstance(tags.get(t), str)
                        and not tags.get(t).strip()
                    )
                ]

                if missing_tags:
                    logger.warning(
                        "⚠️  Group '%s' violates policy. Missing tags: %s",
                        rg.name,
                        missing_tags,
                    )
                    result.non_compliant[rg.name] = missing_tags
                else:
                    logger.info("✅ Group '%s' is fully compliant.", rg.name)
                    result.compliant.append(rg.name)

            logger.info(
                "--- Audit complete. Compliant: %d, Non-compliant: %d ---",
                result.compliant_count,
                result.non_compliant_count,
            )
        # FIX: catch specific Azure exceptions instead of broad Exception
        except ClientAuthenticationError as e:
            logger.error(
                "❌ Authentication failed. Check your credentials and RBAC role assignment: %s",
                e.message,
            )
            raise
        except HttpResponseError as e:
            logger.error(
                "❌ Azure API error (status %s): %s",
                e.status_code,
                e.message,
            )
            raise
        except Exception as e:
            # Fallback for truly unexpected errors (e.g. network issues)
            logger.error(
                "❌ Critical error during audit execution: %s",
                e,
            )
            raise

        return result

    def cleanup_preview(self) -> None:
        """Placeholder for identifying unused resources."""
        logger.info(
            "🔍 Searching for cost optimization opportunities (Preview Mode)..."
        )


if __name__ == "__main__":
    try:
        bot = AzureGovernanceBot()
        bot.audit_tags()
        bot.cleanup_preview()
    except Exception as e:
        logger.critical("Bot failed to start: %s", e)
        raise SystemExit(1) from e

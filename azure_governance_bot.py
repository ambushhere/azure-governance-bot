import logging
import os
from typing import List, Optional

from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient

# Professional logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AzureGovernanceBot")


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
                "AZURE_SUBSCRIPTION_ID must be set as an environment variable or passed to the constructor."
            )
        # Explicitly typed as str (not Optional) after validation
        self.subscription_id: str = _sub_id

        self.credential = DefaultAzureCredential()
        self.client = ResourceManagementClient(self.credential, self.subscription_id)

    def audit_tags(self, mandatory_tags: Optional[List[str]] = None):
        """
        Checks all resource groups for tagging policy compliance.

        Args:
            mandatory_tags: List of required tag keys. Defaults to ["CostCenter", "Owner", "Environment"].
        """
        # FIX: avoid mutable default argument — create a new list each call
        if mandatory_tags is None:
            mandatory_tags = ["CostCenter", "Owner", "Environment"]

        # FIX: mask subscription_id in logs to avoid leaking it to log aggregators
        masked_id = f"***{self.subscription_id[-4:]}"
        logger.info(f"--- Starting tag audit for subscription: {masked_id} ---")

        try:
            resource_groups = self.client.resource_groups.list()
            compliant_count = 0
            non_compliant_count = 0

            for rg in resource_groups:
                tags = rg.tags if rg.tags else {}
                missing_tags = [tag for tag in mandatory_tags if tag not in tags]

                if missing_tags:
                    logger.warning(
                        f"⚠️  Group '{rg.name}' violates policy. Missing tags: {missing_tags}"
                    )
                    non_compliant_count += 1
                else:
                    logger.info(f"✅ Group '{rg.name}' is fully compliant.")
                    compliant_count += 1

            logger.info(
                f"--- Audit complete. Compliant: {compliant_count}, Non-compliant: {non_compliant_count} ---"
            )

        # FIX: catch specific Azure exceptions instead of broad Exception
        except ClientAuthenticationError as e:
            logger.error(
                f"❌ Authentication failed. Check your credentials and RBAC role assignment: {e.message}"
            )
        except HttpResponseError as e:
            logger.error(f"❌ Azure API error (status {e.status_code}): {e.message}")
        except Exception as e:
            # Fallback for truly unexpected errors (e.g. network issues)
            logger.error(
                f"❌ Unexpected error during audit execution: {type(e).__name__}: {e}"
            )
            raise

    def cleanup_preview(self):
        """Placeholder for identifying unused resources."""
        logger.info(
            "🔍 Searching for cost optimization opportunities (Preview Mode)..."
        )
        pass


if __name__ == "__main__":
    try:
        bot = AzureGovernanceBot()
        bot.audit_tags()
        bot.cleanup_preview()
    except Exception as e:
        logger.critical(f"Bot failed to start: {e}")

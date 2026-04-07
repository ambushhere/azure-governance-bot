import os
import logging
from typing import List, Optional
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient

# Professional logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AzureGovernanceBot")

class AzureGovernanceBot:
    """
    Automates resource auditing in Microsoft Azure.
    Helps maintain tagging compliance and optimize costs.
    """

    def __init__(self, subscription_id: Optional[str] = None):
        self.subscription_id = subscription_id or os.getenv("AZURE_SUBSCRIPTION_ID")
        if not self.subscription_id:
            raise ValueError("AZURE_SUBSCRIPTION_ID must be set as an environment variable or passed to the constructor.")

        self.credential = DefaultAzureCredential()
        self.client = ResourceManagementClient(self.credential, self.subscription_id)

    def audit_tags(self, mandatory_tags: List[str] = ["CostCenter", "Owner", "Environment"]):
        """Checks all resource groups for tagging policy compliance."""
        logger.info(f"--- Starting tag audit for subscription: {self.subscription_id} ---")
        
        try:
            resource_groups = self.client.resource_groups.list()
            compliant_count = 0
            non_compliant_count = 0

            for rg in resource_groups:
                tags = rg.tags if rg.tags else {}
                missing_tags = [tag for tag in mandatory_tags if tag not in tags]

                if missing_tags:
                    logger.warning(f"⚠️  Group '{rg.name}' violates policy. Missing tags: {missing_tags}")
                    non_compliant_count += 1
                else:
                    logger.info(f"✅ Group '{rg.name}' is fully compliant.")
                    compliant_count += 1

            logger.info(f"--- Audit complete. Compliant: {compliant_count}, Non-compliant: {non_compliant_count} ---")
            
        except Exception as e:
            logger.error(f"❌ Critical error during audit execution: {str(e)}")

    def cleanup_preview(self):
        """Placeholder for identifying unused resources."""
        logger.info("🔍 Searching for cost optimization opportunities (Preview Mode)...")
        pass

if __name__ == "__main__":
    try:
        bot = AzureGovernanceBot()
        bot.audit_tags()
        bot.cleanup_preview()
    except Exception as e:
        logger.critical(f"Bot failed to start: {e}")
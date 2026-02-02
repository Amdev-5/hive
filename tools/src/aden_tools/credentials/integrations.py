"""
Integration credentials.

Contains credentials for third-party service integrations (HubSpot, etc.).
"""

from .base import CredentialSpec

INTEGRATION_CREDENTIALS = {
    "hubspot": CredentialSpec(
        env_var="HUBSPOT_ACCESS_TOKEN",
        tools=[
            "hubspot_search_contacts",
            "hubspot_get_contact",
            "hubspot_create_contact",
            "hubspot_update_contact",
            "hubspot_search_companies",
            "hubspot_get_company",
            "hubspot_create_company",
            "hubspot_update_company",
            "hubspot_search_deals",
            "hubspot_get_deal",
            "hubspot_create_deal",
            "hubspot_update_deal",
        ],
        required=True,
        startup_required=False,
        help_url="https://developers.hubspot.com/docs/api/private-apps",
        description="HubSpot access token (Private App or OAuth2)",
        # Auth method support
        aden_supported=True,
        aden_provider_name="hubspot",
        direct_api_key_supported=True,
        api_key_instructions="""To get a HubSpot Private App token:
1. Go to HubSpot Settings > Integrations > Private Apps
2. Click "Create a private app"
3. Name your app (e.g., "Hive Agent")
4. Go to the "Scopes" tab and enable:
   - crm.objects.contacts.read
   - crm.objects.contacts.write
   - crm.objects.companies.read
   - crm.objects.companies.write
   - crm.objects.deals.read
   - crm.objects.deals.write
5. Click "Create app" and copy the access token""",
        # Health check configuration
        health_check_endpoint="https://api.hubapi.com/crm/v3/objects/contacts?limit=1",
        health_check_method="GET",
        # Credential store mapping
        credential_id="hubspot",
        credential_key="access_token",
    ),
    "calcom": CredentialSpec(
        env_var="CALCOM_API_KEY",
        tools=[
            "calcom_list_bookings",
            "calcom_get_booking",
            "calcom_create_booking",
            "calcom_cancel_booking",
            "calcom_get_availability",
            "calcom_update_schedule",
            "calcom_list_event_types",
            "calcom_get_event_type",
        ],
        required=True,
        startup_required=False,
        help_url="https://cal.com/docs/api-reference/v1",
        description="Cal.com API key for scheduling and booking management",
        # Auth method support
        aden_supported=False,
        direct_api_key_supported=True,
        api_key_instructions="""To get a Cal.com API key:
1. Log in to Cal.com
2. Go to Settings → Developer → API Keys
3. Click "Create new API key"
4. Give it a name and set expiration
5. Copy the key (shown only once)""",
        # Health check configuration
        health_check_endpoint="https://api.cal.com/v1/me",
        health_check_method="GET",
        # Credential store mapping
        credential_id="calcom",
        credential_key="api_key",
    ),
}

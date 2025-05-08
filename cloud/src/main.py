# Copyright 2024, Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from firebase_functions import logger
import os
import re
import textwrap
from typing import Any, Tuple
import flask
import google.auth
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v18.common.types.custom_parameter import CustomParameter
from google.api_core import exceptions
from google.api_core import protobuf_helpers
from google.api_core.exceptions import DeadlineExceeded
from itertools import batched

_PATTERN = re.compile(r'[^a-zA-Z0-9|;_\/^(!]')

GOOGLE_ADS_LOGIN_CUSTOMER_ID = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
GOOGLE_ADS_DEVELOPER_TOKEN = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
CAMPAIGN_PARAMTER_NAME = os.environ.get("CAMPAIGN_PARAMTER_NAME")

def main(event: dict[str, Any]) -> flask.Response:
    """The entry point of the solution.

    Args:
        event: A dictionary representing the event data payload.

    Returns:
        flask.Response: http response of the function.
    """
    client = get_client()
    customer_ids_list = get_all_customer_ids(client, GOOGLE_ADS_LOGIN_CUSTOMER_ID)

    for current_account in customer_ids_list:
        current_account_id = str(current_account.customer_client.id)
        
        campaigns_to_process = get_all_campaigns_for_current_customer_id(client, current_account_id)
        campaign_operations = []
        for campaign_item in campaigns_to_process:
            campaign_operation, should_update = setup_campaign(client, campaign_item.campaign, CAMPAIGN_PARAMTER_NAME, current_account_id)
            if should_update:
                campaign_operations.append(campaign_operation)
        
        if len(campaign_operations) > 0:
            campaign_service = client.get_service("CampaignService")
            request_batches = list(batched(campaign_operations, 2000))
            for batch in request_batches:
                campaign_response = campaign_service.mutate_campaigns(
                    customer_id=current_account_id,
                    operations=batch,
                )
    return flask.Response(
        flask.json.dumps({
            "status": "Success",
            "message": "Campaigns processing completed",
        }),
        status=200,
        mimetype="application/json",
    )


def get_client()->GoogleAdsClient:
    """Obtain Google Ads client.

    Returns:
        result: GoogleAdsClient client.
    """
    credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/adwords'])
    client = GoogleAdsClient(credentials=credentials, developer_token=GOOGLE_ADS_DEVELOPER_TOKEN, login_customer_id=GOOGLE_ADS_LOGIN_CUSTOMER_ID)
    return client 


def parse_campaign_name(campaign_name: str) -> str:
    """Parse the campaign name.

    Args:
        campaign_name: name of the campaign

    Returns:
        result: parsed name of the campaign.
    """
    result = re.sub(_PATTERN, "_", campaign_name)
    return result


def setup_campaign(
    client: GoogleAdsClient,
    campaign_item: Any,
    campaign_parameter_name: str,
    customer_id:str
)->Tuple[list[Any], bool]:
    """Setup the custom parameter for the current campaign.

    Args:
        client: Google Ads client
        campaign_item: campaign object representation
        campaign_parameter_name: name for the custom parameter that will be created in the campaign
        customer_id: id of the current account

    Returns:
        a tuple containing the operation that needs to be performed (if required) and
            a boolean that specifies if there is any action to be performed.
    """

    campaign_service = client.get_service("CampaignService")
    campaign_operation = client.get_type("CampaignOperation")

    campaign_update = campaign_operation.update
    campaign_update.resource_name = campaign_item.resource_name
    campaign_update.name = campaign_item.name

    initial_name = campaign_item.name
    parsed_campaign_name = parse_campaign_name(initial_name)

    updated_list_of_url_custom_parameters, should_update_the_campaign = add_campaign_name_to_custom_parameters(
        client, campaign_item.url_custom_parameters, campaign_parameter_name, parsed_campaign_name
    )
    if should_update_the_campaign:
        campaign_update.url_custom_parameters.extend(
            updated_list_of_url_custom_parameters
        )
        field_mask = protobuf_helpers.field_mask(campaign_item, campaign_update)

        client.copy_from(campaign_operation.update_mask, field_mask)

    return campaign_operation, should_update_the_campaign



def add_campaign_name_to_custom_parameters(
    client: GoogleAdsClient,
    url_custom_parameters: list[CustomParameter],
    campaign_parameter_name: str,
    parsed_campaign_name:str
)->Tuple[list[CustomParameter], bool]:
    """Setup the custom parameter for the current campaign.

    Args:
        client: Google Ads client
        url_custom_parameters: list of current campaign Custom Parameter objects
        campaign_parameter_name: name for the custom parameter that will be created in the campaign
        parsed_campaign_name: value of the new Custom Parameter

    Returns:
        the list of (possibly) updated Customer Parameters and
            a boolean that specifies if there is any action to be performed.
    """

    updated_url_custom_parameters = []
    found = False

    for custom_param in url_custom_parameters:
        cp = client.get_type("CustomParameter")
        cp.key = custom_param.key
        cp.value = custom_param.value
        if cp.key == campaign_parameter_name:
            if cp.value == parsed_campaign_name:
                # Return the original list without changes
                return url_custom_parameters, False
            
            cp.value = parsed_campaign_name
            found = True
        updated_url_custom_parameters.append(cp)

    if not found:
        # Add new custom parameter since it was missing
        cp_campaign_utm = client.get_type("CustomParameter")
        cp_campaign_utm.key = campaign_parameter_name
        cp_campaign_utm.value = parsed_campaign_name
        updated_url_custom_parameters.append(cp_campaign_utm)

    return updated_url_custom_parameters, True



def get_all_customer_ids(client:GoogleAdsClient, login_customer_id: str)->list[Any]:
    """Gets all the customer ids.

    Args:
      client: The Google Ads client.

    Returns:
        the list of customer ids extracted
    """
    try:
        # Gets instances of the GoogleAdsService and CustomerService clients.
        ga_service = client.get_service("GoogleAdsService")

        # Creates a query that retrieves all child accounts of the manager
        # specified in search calls below.
        query = textwrap.dedent("""
            SELECT
            customer_client.client_customer,
            customer_client.level,
            customer_client.manager,
            customer_client.descriptive_name,
            customer_client.currency_code,
            customer_client.time_zone,
            customer_client.id
            FROM customer_client
            WHERE customer.status='ENABLED'
            """)

        stream = ga_service.search_stream(customer_id=login_customer_id, query=query)

        customer_ids_list = []
        return [row for batch in stream for row in batch.results]
        
    except GoogleAdsException as ex:
        logger.error(f'Error in Customer Id {login_customer_id}')
        logger.error(f'Error in query: {query}')
        logger.error(
            f"Request with ID '{ex.request_id}' failed with status"
            f" {ex.error.code().name} and includes the following errors:"
        )
        for error in ex.failure.errors:
            logger.error(f"\tError with message '{error.message}'")
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    logger.error(f"\t\tOn field '{field_path_element.field_name}'")
        raise Exception(f"Failure on processing GAQL query: {query}")
     




def get_all_campaigns_for_current_customer_id(client:GoogleAdsClient, current_account_id:str)->list[Any]:
    """Retrieve all campaigns (Search, Shopping, DemandGen and PMAX) for current customer .

    Args:
        client: Google Ads client
        current_account_id: id of the current account

    Returns:
        the list of campaigns extracted
    """
    try:
        ga_service = client.get_service("GoogleAdsService")
        query = textwrap.dedent("""
            SELECT
            campaign.id,
            campaign.name,
            campaign.resource_name,
            campaign.url_custom_parameters
            FROM campaign
            WHERE campaign.advertising_channel_type IN ('DEMAND_GEN', 'PERFORMANCE_MAX', 'SEARCH', 'SHOPPING')
            """)

        # Issues a search request using streaming.
        stream = ga_service.search_stream(customer_id=current_account_id, query=query)
        return [row for batch in stream for row in batch.results]
    except GoogleAdsException as ex:
        logger.error(f'Error in Customer Id {current_account_id}')
        logger.error(f'Error in query: {query}')
        logger.error(
            f"Request with ID '{ex.request_id}' failed with status"
            f" {ex.error.code().name} and includes the following errors:"
        )
        for error in ex.failure.errors:
            logger.error(f"\tError with message '{error.message}'")
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    logger.error(f"\t\tOn field '{field_path_element.field_name}'")
        raise Exception(f"Failure on processing GAQL query: {query}")

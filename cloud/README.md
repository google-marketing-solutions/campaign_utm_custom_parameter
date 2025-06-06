## Google Ads - Add UTM custom parameter at campaign level

## Context

Even if auto-tagging is enabled, there are some cases where the Google Click Identifier (GCLID) cannot be used as intended. This can happen, for example, when ad_user_data is denied through your Consent Mode implementation. In these situations, the automatic retrieval of dimensions from the Ads platform might be impacted. As a result, you might see (data not available) labels for cross-channel traffic source dimensions in Google Analytics.

To improve the above, you can implement manual tagging (UTM parameters) alongside auto-tagging. Manual tagging allows you to send traffic source information to Google Analytics by configuring destination URLs with UTM parameters to populate traffic-source dimensions. 

While implementing manual tagging using UTMs, we encourage you to maintain consistency on the values for each of the ads platforms to ensure consistency in your reports and automate as much as possible the collection of the values of UTM parameters.


## Purpose of the custom parameter script


This solution helps to automatically sets a custom parameter at campaign level with the value equals to the name of each campaign.
It allows client to ease their tracking in GA4 with utm. Specifically: utm-campaign

**Attention: this script works only for DemandGen, Search, Shopping and Performance Max campaigns.**

## Setup


### GCP
Open your GCP project and then open the Cloud Shell

1. Clone this repository.
2. Navigate to the terraform folder.
3. Open the file terraform.tfvars and configure each variable.
    1. The solution is configured to run every day at 16:00. If you want to change this, please open edit the Cloud Schduler configuration inside terraform/main.tf at line 110.
4. Download the latest stable version of [Terraform](from https://releases.hashicorp.com/terraform/) selecting the "_amd64.zip" version
5. Unzip it and run the command "sudo mv terraform /usr/bin/"
6. Now run the command "terraform init"
7. Now run the command "terraform apply", this will configure your environment and create all the required components.
8. On GCP left side menu navigate to IAM & Admin -> Service Accounts
9. Copy the full email address of the service account which email starts with "utm-campaign-runner", you will need to add it as a user in Google Ads

### Google Ads
Open your MCC Google Ads account

1.On the left side menu go to Admin -> Access and Security .
2. Now click the "+".
3. Paste the email of the Service Account you've copied at the step #9 in the GCP section and select "Standard" for the access type.
4. Click "Send Invitation".

## Step 2: Add the Google Analytics UTM parameters in the Final URL suffix field

[Final url suffix](https://support.google.com/google-ads/answer/9054021?hl=en) allows you to enter parameters that will be attached to the end of your landing page URL so you can track information about where people go after they click your ad. It can be set at different levels in your account: Account, Campaign, Adgroup, or Ad level.

**If you are not using a tracking tool** (ad management and/or site centric) we recommend to set the utms at the account level:
1. Navigate in the Google Ads account, and go in the Account setting section.
2. There you’ll find a “Tracking” setting.
3. Here you can find the Final URL suffix field.  Set it to: 
utm_source=google&utm_source_platform=Google+Ads&utm_medium=cpc&utm_campaign={_campaignname}&utm_campaignid={campaignid}

**If you are using a tracking tool**, check on your account at every level, where the “final url suffix” field is already filled out. We recommend using [Google Ads Editor](https://support.google.com/google-ads/editor/answer/2484521?hl=en) to check this quickly. 

If some final url suffix is filled, just [download a bulksheet](https://support.google.com/google-ads/editor/answer/15121148?hl=en&ref_topic=13728&sjid=11706207748123949356-NC) of your account.

If they are not using the final URL suffix yet, make sure you set-up a final url suffix at the account level. 

In your bulksheet, add the UTM parameters after your existing final URL suffix:
*"&utm_source=google&utm_source_platform=Google+Ads&utm_medium=cpc&utm_campaign={_campaignname}&utm_campaignid={campaignid}"*

Example: 
- Final URL suffix is already set to “a=1&b=2”.
- Just add after the utm parameters for Google Analytics:
- a=1&b=2*&utm_source=google&utm_source_platform=Google+Ads&utm_medium=cpc&utm_campaign={_campaignname}&utm_campaignid={campaignid}*

**Note that we recommend adding the URL suffix at the highest possible level.**

### Step 3: Verify your tracking

In your Google Ads account, enter in the edition of one of your ads.

In the URL option section, you’ll find a “Test” button. This will allow you to verify that UTM parameters are properly filled. The name of the campaign should be readable.

## License

Apache 2.0; see [`LICENSE`](../LICENSE) for details.

## Disclaimer

This project is not an official Google project. It is not supported by
Google and Google specifically disclaims all warranties as to its quality,
merchantability, or fitness for a particular purpose.
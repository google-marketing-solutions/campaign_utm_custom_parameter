project = {
  name            = "NAME_OF_YOUR_GCP_PROJECT"
}
region = "us-central1" # Region where this project has been created


google_ads_configs = {
  developer_token                     = "YOUR_GOOGLE_ADS_MCC_DEVELOPER_TOKEN"
  login_customer_id                   = "YOUR_GOOGLE_ADS_MCC_LOGIN_CUSTOMER_ID" 
  campaign_parameter_name             = "campaignname" # The name to your Custom parameter that will be created at campaign level
}

google_cloud_configs = {
  time_zone="Europe/Rome" # Your Timezone. E.G. "Europe/Rome"
}
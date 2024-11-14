
// Copyright 2024, Google Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.




//////////////////////////////////// START CUSTOMIZABLE VARIABLES ////////////////////////////////////////////////////////////


const CAMPAIGN_NAME_CUSTOM_PARAMETER = 'campaignname';


// If set to true, it will add the UTM to all your campaigns at campaign level.
// VERIFY your tracking level before setting it to true.
const ADD_TO_CAMPAIGN_FINAL_URL_SUFFIX = false;




//////////////////////////////////// END CUSTOMIZABLE PARAMETERS ////////////////////////////////////////////////////////////


const FINAL_URL_SUFFIX_TRACKER = `utm_source=google&utm_source_platform=GoogleAds&utm_medium=cpc&utm_campaign={_${CAMPAIGN_NAME_CUSTOM_PARAMETER}}&utm_campaignid={campaignid}`;
const CUSTOM_PARAMETER_NAME_CHECK = new RegExp("^[a-zA-Z0-9]{1,16}$");




/**
* Entry point of the script
* 
* @public
*/
function main(){
  if( !isCustomParameterNameValid_() ){
    throw new Error(`The selected custom parameter name (${CAMPAIGN_NAME_CUSTOM_PARAMETER}) is not valid!`);
  }


  // Process account according to the type of account this script is running on. 
  if( isThisAccountMCC_() ) {
    processMCCaccounts_();
  }
  else {
    processSingleAccount_();
  }
}


/**
 * Checks if current account where the script is running is MCC or not
 *
 * @return {boolean}
 */
function isThisAccountMCC_() {
  return !!this.AdsManagerApp;
}




/**
 * Iterates every sub account of the MCC account and starts processing them one by one.
* 
* @private 
*/
function processMCCaccounts_(){


  // Get Accounts Iterator for all sub accounts
  const accountIterator = AdsManagerApp.accounts().get();


  // Iterate over subaccounts
  while ( accountIterator.hasNext() ) {
    const currentAccount = accountIterator.next();
    AdsManagerApp.select( currentAccount );
    processSingleAccount_();
  }
}




/**
* Sets current account and starts the processing of its campaigns
* 
* @private 
*/
function processSingleAccount_() {
  const currentAccount = AdsApp.currentAccount().getName();
  Logger.log(`Processing Account "${currentAccount}"`);


  // Retrieve list of campaigns for the account
  const campaignIterator = AdsApp.campaigns().get();
  // Process account's campaigns if there are records
  if(!!campaignIterator && campaignIterator.hasNext()){
    addCustomParameterToCampaigns_(campaignIterator, CAMPAIGN_NAME_CUSTOM_PARAMETER);
  }


  // Retrieve list of Shopping campaigns for the account
  const shoppingCampaignIterator = AdsApp.shoppingCampaigns().get();
  // Process account's Shopping campaigns if there are records
  if(!!shoppingCampaignIterator && shoppingCampaignIterator.hasNext()){
    addCustomParameterToCampaigns_(shoppingCampaignIterator, CAMPAIGN_NAME_CUSTOM_PARAMETER);
  }
  
  // Retrieve list of PMAX campaigns for the account
  const pMaxCampaignIterator = AdsApp.performanceMaxCampaigns().get();
  // Process account's PMAX campaigns if there are records
  if(!!pMaxCampaignIterator && pMaxCampaignIterator.hasNext()){
    addCustomParameterToCampaigns_(pMaxCampaignIterator, CAMPAIGN_NAME_CUSTOM_PARAMETER);
  }
}


/**
* checks, for all of the Campaigns in the provided iterator, 
* if the campaign name custom parameter named as per variable exists 
* and in case it doesn't, it creates it
* If you flag ADD_TO_CAMPAIGN_FINAL_URL_SUFFIX has been enabled,
* it also adds the UTMS to the campaign final url suffix.
* 
* @param{!object} iterator: Iterator object that contains a collection of elements to check. 
* @param{string} customParameterName: name of the campaign parameter
* @private 
*/
function addCustomParameterToCampaigns_(iterator, customParameterName){
  while (iterator.hasNext()) {
    
    // Get required objects
    const currentCampaign = iterator.next();
    const currentCampaignURL = currentCampaign.urls();
    const currentCampaignParameters = currentCampaignURL.getCustomParameters();
    try {
      const currentCampaignName = replaceInvalidSymbolsInCampaignName_(currentCampaign.getName());


      // Update/Create Custom Paramter either if missing or campaign name has changed 
      if( Object.keys(currentCampaignParameters).indexOf( customParameterName ) === -1  ||
    currentCampaignParameters[ customParameterName ] !== currentCampaignName) {
        currentCampaignParameters[ customParameterName ] = currentCampaignName;
        currentCampaign.urls().setCustomParameters(currentCampaignParameters);
      }


      // IF YOU SELECTED it will append the parameters to the campaign url suffix
      if( ADD_TO_CAMPAIGN_FINAL_URL_SUFFIX){
        // No need to update the final url suffix if it already contains the parameters we want to add
        currentCampaignFinalUrlSuffix = currentCampaignURL.getFinalUrlSuffix();
        if( !!currentCampaignFinalUrlSuffix && currentCampaignFinalUrlSuffix.indexOf(FINAL_URL_SUFFIX_TRACKER) !== -1 ){
          return;
        }


        // If the tracking parameter is in place
        if( !currentCampaignFinalUrlSuffix ){
          currentCampaignFinalUrlSuffix = FINAL_URL_SUFFIX_TRACKER;
        }
        else{
          currentCampaignFinalUrlSuffix += `&${FINAL_URL_SUFFIX_TRACKER}`;
        }
        currentCampaignURL.setFinalUrlSuffix(currentCampaignFinalUrlSuffix); 
      }
    }catch(e){
        Logger.log(`Campaign name missing for campaign ID ${currentCampaign.getId()}`);
    }
  }
}




/**
* Checks if the selected custom paramter name is valid
* 
* @return{boolean} if the custom parameter name is valid or not
* @private 
*/
function isCustomParameterNameValid_() {
   const match = CAMPAIGN_NAME_CUSTOM_PARAMETER.match(CUSTOM_PARAMETER_NAME_CHECK);
   return match && CAMPAIGN_NAME_CUSTOM_PARAMETER === match[0];
}






/**
* Replaces invalid characters in campaign name 
* according to Custom Parameter accepted values:
* https://support.google.com/google-ads/answer/6325879?hl=en
* 
* @param{string} campaignName: name of the campaign
* @return{string} campaign name cleaned of unsupported characters
* @private 
*/
function replaceInvalidSymbolsInCampaignName_(campaignName){
  let newCampaignName = campaignName;
  if(!newCampaignName){
     throw new Error('Missing campaign name!');
  }
  if(newCampaignName.length > 250){
    newCampaignName= newCampaignName.substr(0, 250);
  }
  return newCampaignName.replace(/[^a-zA-Z0-9|;_\/^(!]/g, "_");
}

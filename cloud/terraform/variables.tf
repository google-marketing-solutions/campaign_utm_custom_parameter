# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.




variable "project" {
  description = "Project configuration."
  type = object({
    name = string
  })
}

variable "region" {
  type        = string
  description = "The region to deploy the resources to, e.g. europe-west2"
  default     = "europe-west2"
}


variable "google_ads_configs" {
  description = "Google Ads configurations"
  type = object({
    developer_token                     = string
    login_customer_id                   = string
    campaign_parameter_name             = string
  })
}

variable "google_cloud_configs" {
  description = "Google Cloud configurations"
  type = object({
    time_zone     = string
  })
}
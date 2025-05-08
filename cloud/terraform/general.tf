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

/** LOCAL_VARIABLES */
locals {
  source_files = ["../src/main.py", "../src/requirements.txt"]
}


/** LOCAL_VARIABLES */
locals {
  cloud-function-dir = "../src/"
  cloud-function-test-files = [ # explicit list of files to exclude
    "main_test.py"
  ]
}

/** ARCHIVE_FILE */
data "archive_file" "campaign_utm_gads_bucket" {
  type        = "zip"
  output_path = ".temp/campaign_utm_gads.zip"
  source_dir  = local.cloud-function-dir
  excludes    = [for file in fileset(local.cloud-function-dir, "**") : file if contains(local.cloud-function-test-files, file)]
}

/** BUCKET STORAGE */
resource "google_storage_bucket" "campaign_utm_gads_source_archive_bucket" {
  name                        = "${module.project.project_id}-campaign-utm-gads-src-arch-bucket"
  project                     = module.project.project_id
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "Delete"
    }
  }
}


/** BUCKET OBJECTS */
resource "google_storage_bucket_object" "campaign_utm_gads_bucket_object" {
  name   = "campaign_utm_gads_${data.archive_file.campaign_utm_gads_bucket.output_md5}.zip"
  bucket = google_storage_bucket.campaign_utm_gads_source_archive_bucket.name
  source = data.archive_file.campaign_utm_gads_bucket.output_path
}

/** CLOUD FUNCTIONS */
resource "google_cloudfunctions2_function" "campaign_utm_gads" {
  project     = module.project.project_id
  location    = var.region
  name        = "campaign-utm-gads"
  description = "Create custom parameter at campaign level containing the (parsed) campaign name as value"

  service_config {
    available_memory      = "1024M"
    timeout_seconds       = 1800
    service_account_email = module.service-account.email
    ingress_settings      = "ALLOW_ALL"

    environment_variables = {
      GOOGLE_ADS_LOGIN_CUSTOMER_ID = "${var.google_ads_configs.login_customer_id}"
      CAMPAIGN_PARAMTER_NAME = "${var.google_ads_configs.campaign_parameter_name}"
    }
    secret_environment_variables {
      key        = "GOOGLE_ADS_DEVELOPER_TOKEN"
      project_id = module.project.project_id
      secret     = google_secret_manager_secret.developer_token.secret_id
      version    = "latest"
    }
  }

  build_config {
    runtime         = "python312"
    entry_point     = "main" # Set the entry point
    service_account = module.service-account.id
    source {
      storage_source {
        bucket = google_storage_bucket.campaign_utm_gads_source_archive_bucket.name
        object = google_storage_bucket_object.campaign_utm_gads_bucket_object.name
      }
    }
  }

  depends_on = [null_resource.iam_wait]
}



/** CLOUD SCHEDULER JOB */
resource "google_cloud_scheduler_job" "campaign_utm_gads" {
  project          = module.project.project_id
  name             = "schedule-utm-campaign-gads"
  description      = "Run the update of the campaign utm mapping on GAds"
  schedule         = "00  16 * * *" # Every day at 16:00
  time_zone        = var.google_cloud_configs.time_zone
  attempt_deadline = "320s"
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.campaign_utm_gads.service_config[0].uri
    body        = base64encode("")
    headers = {
      "Content-Type" = "application/json"
    }
    oidc_token {
      audience              = "${google_cloudfunctions2_function.campaign_utm_gads.service_config[0].uri}/"
      service_account_email = module.service-account.email
    }
  }
}

/** SECRET */
resource "google_secret_manager_secret" "developer_token" {
  project   = module.project.project_id
  secret_id = "campaign-utm-gads-developer-token"
  replication {
    auto {}
  }
}


/** SECRET MANAGER */
resource "google_secret_manager_secret_version" "developer_token" {
  secret      = google_secret_manager_secret.developer_token.id
  secret_data = var.google_ads_configs.developer_token
}
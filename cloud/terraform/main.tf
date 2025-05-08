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

# module "project_creator"

module "project" {
  source         = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/project?ref=v30.0.0"
  name           = var.project.name
  project_create = false
  services = [
    "composer.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "secretmanager.googleapis.com",
    "storage-component.googleapis.com",
    "cloudkms.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudscheduler.googleapis.com",
    "run.googleapis.com",
    "servicecontrol.googleapis.com",
    "servicemanagement.googleapis.com",
    "connectors.googleapis.com",
    "googleads.googleapis.com"
  ]
}

resource "time_sleep" "wait" {
  depends_on      = [module.project.id]
  create_duration = "180s"
}

resource "null_resource" "iam_wait" {
  depends_on = [
    google_project_iam_member.cloudfunctions,
    time_sleep.wait,
    module.service-account
  ]
}

resource "google_project_iam_member" "cloudfunctions" {
  project = module.project.id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${module.project.service_accounts.robots.cloudfunctions}"
}

module "service-account" {
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/iam-service-account?ref=v30.0.0"
  project_id = module.project.id
  name       = "utm-campaign-runner"
  iam_project_roles = {
    (module.project.id) = [
      "roles/datastore.user",
      "roles/cloudfunctions.invoker",
      "roles/run.invoker",
      "roles/cloudscheduler.serviceAgent",
      "roles/pubsub.editor",
      "roles/pubsub.publisher",
      "roles/secretmanager.admin",
      "roles/secretmanager.secretAccessor",
      "roles/storage.objectCreator",
      "roles/storage.objectViewer",
      "roles/artifactregistry.writer"
    ]
  }
}

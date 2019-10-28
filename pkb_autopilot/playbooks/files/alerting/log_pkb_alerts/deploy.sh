#!/bin/sh

FUNCTION="logPkbAlerts"
PROJECT="smu-benchmarking"
BUCKET="smu_pkb_run_logs"
ENV_VARS_FILE="env_vars.yaml"

# set the gcloud project
gcloud config set project ${PROJECT}

gcloud functions deploy logPkbAlerts \
    --runtime python37 \
    --env-vars-file ${ENV_VARS_FILE} \
#    --trigger-http
    --trigger-resource ${BUCKET} \
    --trigger-event google.storage.object.finalize

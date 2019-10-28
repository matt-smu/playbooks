
# Cloudfunction for BigQuery Alerting 

main.py contains the cloudfunction logic. 

deploy.sh is a helper script to manage deployment flags

env_vars.yaml holds the configurable parameters for the alert conditions

## Setup
There are a couple ways to test the function before deploying...

To test locally

Create a python 3.7 virtualenv [env] and install the requirements [pip install -r requirements.txt].

The deploy.sh script should be edited to ensure trigger-http flag is set (not trigger-resource)

In main.py update the environment variables as needed since env_vars.yaml is only used by cloudfunctions

Now run python main.py to start the function in flask

And call the function curl localhost:8000

Once testing is completed edit deploy.sh to disable http trigger and enable resource-trigger with the appropriate bucket name. 

Redeploy with ./deploy.sh


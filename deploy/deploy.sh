#!/bin/sh
echo "Deploying  - start time: $(date)"

# 0.0 create service principal (rbac) for deployinw with Github Actions
# az ad sp create-for-rbac --name azure_cicd_cred --sdk-auth

# 0.1 set the required secrets in github Project, Settings and variables 
#   client-id: ${{ secrets.AZUREAPPSERVICE_CICD_CLIENTID }}
#   tenant-id: ${{ secrets.AZUREAPPSERVICE_CICD_TENANTID }}
#   subscription-id: ${{ secrets.AZUREAPPSERVICE_CICD_SUBSCRIPTIONID }}


#1. resource group
az group create \
    --name weed-detection-resources-group \
    --location westus2

#2. create app service plan
az appservice plan create \
    --name weed-detection-services-plan \
    --resource-group weed-detection-resources-group \
    --sku S1 \
    --is-linux

#3. create the web app itself (note: this is the app service)
az webapp create \
   --name aiweeddetectionapi \
   --plan weed-detection-services-plan \
   --resource-group weed-detection-resources-group \
   --runtime "PYTHON|3.12"


#4. MANUAL via portal: environment 2 variables to be set - the only environment variables that need to be set, 
#     everything else is in the Azure Application Configuration outside this app
#    - ConfigSource=AzureAppConfiguration
#    - AzureConfigConnectionString=<your Azure App Configuration Connectstring>

#5. set the startup command
az webapp config set \
   --name aiweeddetectionapi \
   --resource-group weed-detection-resources-group \
   --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app"

#6. add environment variables
az webapp config appsettings set \
    --name aiweeddetectionapi \
    --resource-group weed-detection-resources-group \
    --settings "AzureConfigConnectionString=

az webapp config appsettings set \
    --name aiweeddetectionapi \
    --resource-group weed-detection-resources-group \
    --settings ConfigSource=AzureAppConfiguration

# Get the current date in YYMMDDHHMM format
BUILD_DATE=$(date +"%y%m%d.%H%M")
az appconfig kv set --name grassdetectionappconfig --key ApiBuildDate --value $BUILD_DATE --yes
    

#6. setup deployment to deploy from github repo- it performs the deployment from the github repo to the app service
#  Note: Azure CLI does not have a direct "redeploy" command for Azure Web Apps. 
#  However, you can achieve a redeployment by reconfiguring the deployment source 
#  or by using the az webapp deployment commands to push the latest changes.
az webapp deployment source config \
   --name aiweeddetectionapi \
   --resource-group weed-detection-resources-group \
   --repo-url https://github.com/kowusu01/AIWeedDetectionAPI.git \
   --branch main 


echo "Deployed: $(date)"


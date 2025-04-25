#!/bin/bash
# Script to deploy the Quiz API to Azure Kubernetes Service (AKS)

# Set variables
RESOURCE_GROUP="QuizApiResourceGroup"
LOCATION="eastus"
ACR_NAME="quizapiregistry"  # Must be globally unique
AKS_CLUSTER="quizapi-aks-cluster"
FLASK_IMAGE="quizapp-flask"
NGINX_IMAGE="quizapp-nginx"
IMAGE_TAG="latest"
HOSTNAME="quizapi.example.com"  # Change to your actual domain

# Export variables for envsubst
export ACR_NAME
export HOSTNAME

# Login to Azure
az login

# Create a resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Login to ACR
az acr login --name $ACR_NAME

# Build the Flask Docker image from root Dockerfile
docker build --platform linux/amd64 -t $FLASK_IMAGE:$IMAGE_TAG .
if [ $? -ne 0 ]; then
    echo "Error: Failed to build Flask Docker image."
    exit 1
fi

# Check if Dockerfile.nginx exists
if [ ! -f "Dockerfile.nginx" ]; then
    echo "Error: Dockerfile.nginx does not exist at the root level."
    exit 1
fi

# Build the NGINX Docker image
docker build --no-cache --platform linux/amd64 -t $NGINX_IMAGE:$IMAGE_TAG -f Dockerfile.nginx .
if [ $? -ne 0 ]; then
    echo "Error: Failed to build NGINX Docker image."
    exit 1
fi

# Tag the images for ACR
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
docker tag $FLASK_IMAGE:$IMAGE_TAG $ACR_LOGIN_SERVER/$FLASK_IMAGE:$IMAGE_TAG
docker tag $NGINX_IMAGE:$IMAGE_TAG $ACR_LOGIN_SERVER/$NGINX_IMAGE:$IMAGE_TAG

# Push the images to ACR
docker push $ACR_LOGIN_SERVER/$FLASK_IMAGE:$IMAGE_TAG
docker push $ACR_LOGIN_SERVER/$NGINX_IMAGE:$IMAGE_TAG

# Create AKS cluster
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_CLUSTER \
  --node-count 1 \
  --node-vm-size Standard_D2s_v3 \
  --enable-addons monitoring \
  --generate-ssh-keys \
  --attach-acr $ACR_NAME

# Get AKS credentials
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER

# Generate deployment.yaml from template
envsubst < deployment.yaml.template > deployment.yaml

# Apply Kubernetes configuration
kubectl apply -f deployment.yaml

# Wait for service to get external IP
kubectl get service quizapp-service --watch
#!/bin/bash

# cleanup resource script
RESOURCE_GROUP="QuizApiResourceGroup"
AKS_CLUSTER="quizapi-aks-cluster"

# Login to Azure
az login

# Delete the AKS cluster (most costly resource)
echo "Deleting AKS cluster $AKS_CLUSTER..."
az aks delete --name $AKS_CLUSTER --resource-group $RESOURCE_GROUP --yes


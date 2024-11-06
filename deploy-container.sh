#!/bin/bash

# Silently, install jq if not already installed
sudo apt-get install -y jq > /dev/null

# Parse and export variables from metadata json file for container access
echo -e "Reading, parsing, and exporting container details..."
while IFS="=" read -r key value; do
  value=$(echo $value | sed 's/^"//;s/"$//')
  export "$key"="$value"
done < <(jq -r 'to_entries|map("\(.key)=\(.value)")|.[]' metadata.json)

echo -e "Details parsed and exported successfully!\n"

# Create new path segment
ROUTE="/api/${CONTAINER_LABEL}/.*"
CONTAINER_SERVICE="${CONTAINER_LABEL}-srv"

# Create container namespace
echo -e "Creating container namespace..."
envsubst < container-ns-template.yml | kubectl apply -f -

# Apply secret configuration onto the new container
echo -e "\nApplying secrets..."
envsubst < secret.yml | kubectl apply -f -

# Create container deployment and service
echo -e "\nCreating container deployment and services..."
envsubst < container-depl-template.yml | kubectl apply -f -

# Apply container routing
echo -e "\nApplying gateway routing..."
envsubst < container-route-template.yml | kubectl apply -f -

echo -e "Container information ${CONTAINER_LABEL} updated successfully!"

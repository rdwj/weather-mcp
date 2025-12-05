#!/bin/bash
# Simple deployment script for MCP server to OpenShift
# Usage: ./deploy.sh [project-name]

set -e

PROJECT=${1:-mcp-demo}

echo "========================================="
echo "MCP Server Deployment to OpenShift"
echo "========================================="
echo "Project: $PROJECT"
echo ""

# Check if logged in to OpenShift
if ! oc whoami &>/dev/null; then
    echo "Error: Not logged in to OpenShift. Please run 'oc login' first."
    exit 1
fi

# Create project if it doesn't exist
echo "→ Setting up project..."
if oc project $PROJECT &>/dev/null; then
    echo "  Using existing project: $PROJECT"
else
    echo "  Creating new project: $PROJECT"
    oc new-project $PROJECT
fi

# Create secret from .env if it exists and has NOAA key
if [ -f .env ]; then
    NOAA_KEY=$(grep -E '^NOAA_CDO_TOKEN=' .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' || true)
    if [ -n "$NOAA_KEY" ]; then
        echo "→ Creating/updating weather-mcp-secrets..."
        oc create secret generic weather-mcp-secrets \
            --from-literal=noaa-cdo-token="$NOAA_KEY" \
            --dry-run=client -o yaml | oc apply -f - -n $PROJECT
    else
        echo "→ No NOAA_CDO_TOKEN in .env, historical weather will not be available"
    fi
else
    echo "→ No .env file found, historical weather will not be available"
fi

# Apply OpenShift resources
echo "→ Applying OpenShift resources..."
sed "s|image: mcp-server:latest|image: image-registry.openshift-image-registry.svc:5000/$PROJECT/mcp-server:latest|g" openshift.yaml | oc apply -f - -n $PROJECT

# Clean up old deployment
echo "→ Cleaning up old deployment..."
if oc get deployment mcp-server -n $PROJECT &>/dev/null; then
    echo "  Scaling down deployment to remove old pods..."
    oc scale deployment/mcp-server --replicas=0 -n $PROJECT 2>/dev/null || true
    echo "  Waiting for pods to terminate..."
    oc wait --for=delete pod -l app=mcp-server -n $PROJECT --timeout=60s 2>/dev/null || echo "  No pods to clean up"
else
    echo "  No existing deployment found"
fi

# Start build
echo "→ Building container image..."
echo "  Starting binary build from current directory..."
oc start-build mcp-server --from-dir=. --follow -n $PROJECT

# Scale back up and deploy
echo "→ Deploying application..."
echo "  Scaling deployment to 1 replica..."
oc scale deployment/mcp-server --replicas=1 -n $PROJECT
echo "  Waiting for rollout to complete..."
oc rollout status deployment/mcp-server -n $PROJECT --timeout=300s

# Get route
ROUTE=$(oc get route mcp-server -n $PROJECT -o jsonpath='{.spec.host}' 2>/dev/null || echo "")

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
if [ -n "$ROUTE" ]; then
    echo "MCP Server URL: https://$ROUTE/"
    echo ""
    echo "Test with MCP Inspector:"
    echo "  npx @modelcontextprotocol/inspector https://$ROUTE/"
    echo ""
    echo "Note: Route is configured to serve MCP at /mcp path"
else
    echo "Warning: Could not retrieve route URL"
fi
echo "========================================="
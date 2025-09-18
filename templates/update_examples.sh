#!/bin/bash

BACKEND_URL="${BACKEND_SERVICE_URL:-http://localhost:8000}"
GITLAB_API="https://gitlab.com/api/v4"
AUTH_HEADER="Authorization: Bearer $GITLAB_TOKEN"

# Function to delete repo if exists
delete_repo_if_exists() {
    local repo_name="$1"
    
    # Get project ID
    project_id=$(curl -s -H "$AUTH_HEADER" \
        "$GITLAB_API/groups/$EXAMPLES_GROUP_ID/projects?search=$repo_name" \
        | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    
    if [[ -n "$project_id" ]]; then
        echo "🗑️  Deleting existing $repo_name..."
        curl -s -X DELETE -H "$AUTH_HEADER" \
            "$GITLAB_API/projects/$project_id" > /dev/null
        sleep 2  # Wait for deletion to complete
    fi
}

# Stack-based project types (require stack)
declare -a stack_types=(
    "python,library"
    "python,microservice"
    "dotnet,library"
    "dotnet,microservice"
    "nodejs,library"
    "nodejs,microservice"
    "maven,library"
    "maven,microservice"
)

# Cluster-based project types (require clusters)
declare -a cluster_types=(
    "python,monorepo"
    "dotnet,monorepo"
    "nodejs,monorepo"
    "maven,monorepo"
    "delivery"
)

echo "🚀 Updating example repositories..."

# Create stack-based examples
for combo in "${stack_types[@]}"; do
    IFS=',' read -r stack type <<< "$combo"
    repo_name="example-$type-$stack"
    
    delete_repo_if_exists "$repo_name"
    
    payload="{\"project_name\":\"$repo_name\",\"group_id\":\"$EXAMPLES_GROUP_ID\",\"project_type\":\"$type\",\"stack\":\"$stack\"}"
    
    response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -H "$AUTH_HEADER" \
        -d "$payload" \
        "$BACKEND_URL/generate-repo")
    
    http_code="${response: -3}"
    if [[ "$http_code" == "200" ]]; then
        echo "✅ Created $repo_name"
    else
        echo "❌ Failed to create $repo_name (HTTP $http_code)"
    fi
done

# Create cluster-based examples
for combo in "${cluster_types[@]}"; do
    if [[ "$combo" == "delivery" ]]; then
        # Delivery type has no stack
        repo_name="example-delivery"
        payload="{\"project_name\":\"$repo_name\",\"group_id\":\"$EXAMPLES_GROUP_ID\",\"project_type\":\"delivery\",\"clusters\":[{\"name\":\"example-cluster\",\"environment\":\"dev\"}]}"
    else
        # Monorepo types have both stack and clusters
        IFS=',' read -r stack type <<< "$combo"
        repo_name="example-$type-$stack"
        payload="{\"project_name\":\"$repo_name\",\"group_id\":\"$EXAMPLES_GROUP_ID\",\"project_type\":\"$type\",\"stack\":\"$stack\",\"clusters\":[{\"name\":\"example-cluster\",\"environment\":\"dev\"}]}"
    fi
    
    delete_repo_if_exists "$repo_name"
    
    response=$(curl -s -w "%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -H "$AUTH_HEADER" \
        -d "$payload" \
        "$BACKEND_URL/generate-repo")
    
    http_code="${response: -3}"
    if [[ "$http_code" == "200" ]]; then
        echo "✅ Created $repo_name"
    else
        echo "❌ Failed to create $repo_name (HTTP $http_code)"
    fi
done

echo "✅ Example repositories update complete!"
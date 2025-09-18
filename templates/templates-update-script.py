#!/usr/bin/env python3
"""Script to update example repositories from templates CI"""

import os
import requests
import asyncio
from typing import List, Dict

# Configuration from CI variables
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
EXAMPLES_GROUP_ID = os.getenv('EXAMPLES_GROUP_ID')
BACKEND_SERVICE_URL = os.getenv('BACKEND_SERVICE_URL', 'http://localhost:8000')

# Define your stack/type combinations
COMBINATIONS = [
    ('python', 'library'),
    ('python', 'microservice'),
    ('dotnet', 'library'),
    ('dotnet', 'microservice'),
    ('nodejs', 'library'),
    ('maven', 'library'),
    ('maven', 'microservice'),
    ('python', 'monorepo'),
    ('dotnet', 'delivery'),
]

def create_example_repo(stack: str, project_type: str):
    """Call your backend service to create example repo"""
    repo_name = f"example-{project_type}-{stack}"
    
    payload = {
        "project_name": repo_name,
        "group_id": EXAMPLES_GROUP_ID,
        "project_type": project_type,
        "stack": stack,
        "clusters": [{"name": "example-cluster", "environment": "dev"}] 
                   if project_type in ['monorepo', 'delivery'] else None
    }
    
    # Use admin token for authentication
    headers = {"Authorization": f"Bearer {GITLAB_TOKEN}"}
    
    response = requests.post(
        f"{BACKEND_SERVICE_URL}/generate-repo",
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ Created {repo_name}")
    else:
        print(f"❌ Failed to create {repo_name}: {response.text}")

def main():
    print("🚀 Updating example repositories...")
    
    for stack, project_type in COMBINATIONS:
        try:
            create_example_repo(stack, project_type)
        except Exception as e:
            print(f"❌ Error creating {stack}-{project_type}: {e}")
    
    print("✅ Example repositories update complete!")

if __name__ == "__main__":
    main()
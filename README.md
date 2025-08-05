# GitLab Repository Sculptor

A FastAPI-based service that automatically creates and initializes GitLab repositories with pre-configured templates based on project type and technology stack.

## Features

- **OAuth Integration**: Secure GitLab OAuth authentication
- **Multi-Stack Support**: Maven, Node.js, Python, and .NET projects
- **Project Types**: Library, Microservice, Monorepo, and Delivery projects
- **Template Management**: S3-based template storage with Jinja2 processing
- **Automated Setup**: Complete repository initialization with CI/CD, Dockerfiles, and configuration files

## Quick Start

### Prerequisites

- Python 3.8+
- GitLab account with OAuth application configured
- AWS S3 bucket with project templates
- Environment variables configured

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Environment Configuration

Create a `.env` file with the following variables:

```env
GITLAB_CLIENT_ID=your_gitlab_client_id
GITLAB_CLIENT_SECRET=your_gitlab_client_secret
GITLAB_REDIRECT_URI=http://localhost:8000/callback
GITLAB_TOKEN_URL=https://gitlab.com/oauth/token
S3_BUCKET=your-templates-bucket
S3_REGION=us-east-1
LOG_LEVEL=INFO
PORT=8000
```

### Running the Application

```bash
# Development mode
python main.py

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication

#### `GET /login`
Redirects to GitLab OAuth login page.

#### `GET /callback`
Handles OAuth callback and returns access token.

**Response:**
```json
{
  "access_token": "gitlab_access_token",
  "token_type": "Bearer",
  "expires_in": 7200
}
```

### Repository Management

#### `GET /groups`
Retrieves user's accessible GitLab groups.

**Query Parameters:**
- `access_token` (string): GitLab access token

**Response:**
```json
{
  "groups": [
    {"id": 123, "group": "my-organization/team"}
  ]
}
```

#### `POST /generate-repo`
Creates and initializes a new GitLab repository.

**Request Body:**
```json
{
  "access_token": "gitlab_access_token",
  "repo": {
    "project_name": "my-new-project",
    "group_id": "123",
    "project_type": "microservice",
    "stack": "python",
    "deployment_clusters": [
      {"name": "dev", "environment": "development"}
    ]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "repo_url": "https://gitlab.com/group/project",
  "project_id": 456,
  "files_created": [".gitlab-ci.yml", "Dockerfile", "README.md"],
  "message": "Project created and initialized successfully"
}
```

## Project Types & Stacks

### Supported Project Types

| Type | Description | Required Fields |
|------|-------------|----------------|
| `library` | Reusable code library | `stack` |
| `microservice` | Standalone service | `stack` |
| `monorepo` | Multi-service repository | `deployment_clusters` |
| `delivery` | Deployment configuration | `deployment_clusters` |

### Supported Technology Stacks

- **Maven** (`maven`): Java projects with Maven build system
- **Node.js** (`node`): JavaScript/TypeScript projects with npm
- **Python** (`python`): Python projects with pip
- **.NET** (`dotnet`): C# projects with NuGet

## Template Structure

Templates are stored in S3 with the following structure:

```
templates/
├── common/
│   ├── config/           # Stack-specific config files
│   ├── build/           # Dockerfiles and build configs
│   └── gitignore/       # Stack-specific .gitignore files
├── library/             # Library project templates
├── microservice/        # Microservice project templates
├── monorepo/           # Monorepo project templates
└── delivery/           # Delivery project templates
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │  ProjectCreator  │    │ TemplateProcessor│
│   Routes        │───▶│  Service         │───▶│   (S3 + Jinja2) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│   GitLab        │    │   AWS S3         │
│   API Service   │    │   Templates      │
└─────────────────┘    └──────────────────┘
```

## Development

### Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes.py          # FastAPI route definitions
│   ├── core/
│   │   ├── config.py          # Application configuration
│   │   └── logger.py          # Logging setup
│   ├── schemas/
│   │   └── repo_models.py     # Pydantic models
│   └── services/
│       ├── gitlab_service.py  # GitLab API integration
│       ├── project_creator.py # Project orchestration
│       └── template_processor.py # Template processing
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
└── .env                      # Environment variables
```

### Adding New Project Types

1. Create template directory in S3: `templates/{project_type}/`
2. Add templates for CI/CD, README, and Helm charts
3. Update validation logic in `routes.py`
4. Add project type to `repo_models.py`

### Adding New Technology Stacks

1. Add stack to `StackType` enum in `repo_models.py`
2. Update `_SUPPORTED_STACKS` in `template_processor.py`
3. Add stack-specific templates to S3:
   - `templates/common/config/{stack}.config`
   - `templates/common/build/Dockerfiles/{stack}.Dockerfile`
   - `templates/common/gitignore/{stack}.gitignore`

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid token)
- `403` - Forbidden (insufficient permissions)
- `500` - Internal Server Error
- `502` - Bad Gateway (external service error)

## Security

- OAuth 2.0 authentication with GitLab
- Access tokens for API authorization
- Input validation with Pydantic models
- CORS configuration for web clients

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
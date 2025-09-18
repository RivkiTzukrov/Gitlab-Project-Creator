# GitLab Repository Sculptor

FastAPI service that automatically creates GitLab repositories with pre-configured templates based on project type and technology stack.

## Features

- **GitLab OAuth Authentication** - Secure token-based authentication
- **Multi-Stack Support** - Maven, Node.js, Python, .NET projects
- **Project Templates** - Library, Microservice, Monorepo, Delivery types
- **S3 Template Storage** - Jinja2-processed templates with custom delimiters
- **CI/CD Variables** - Automatic cluster configuration for deployment projects
- **Private S3 Support** - Works with internal S3-compatible services

## Quick Start

### Prerequisites

- Python 3.8+
- GitLab OAuth application
- S3 bucket with templates
- Environment variables

### Installation

```bash
git clone <repository-url>
cd backend
pip install -r requirements.txt
```

### Configuration

Create `.env` file:

```env
GITLAB_CLIENT_ID=your_client_id
GITLAB_CLIENT_SECRET=your_client_secret
GITLAB_REDIRECT_URI=http://localhost:8000/callback
S3_BUCKET=your-templates-bucket
S3_ENDPOINT_URL=https://your-s3-endpoint  # Optional for private S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Run

```bash
python main.py
```

## API Usage

### Authentication

1. **GET /login** - Redirect to GitLab OAuth
2. **GET /callback** - Handle OAuth callback, get access token

### Repository Operations

**GET /groups** - Get user's GitLab groups
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/groups
```

**POST /generate-repo** - Create repository with templates
```json
{
  "project_name": "My Project",
  "group_id": "123",
  "project_type": "microservice",
  "stack": "python",
  "clusters": [{"name": "dev-cluster", "environment": "dev"}]
}
```

## Project Types

| Type | Description | Requirements |
|------|-------------|-------------|
| `library` | Code library | `stack` |
| `microservice` | Standalone service | `stack` |
| `monorepo` | Multi-service repo | `stack`, `clusters` |
| `delivery` | Deployment config | `clusters` |

## Template System

Templates use Jinja2 with custom delimiters to avoid conflicts with Helm:
- **Jinja2 variables**: `{% variable_name %}`
- **Jinja2 blocks**: `{# if condition #}`
- **Helm variables**: `{{ .Values.name }}` (unchanged)

### S3 Structure

```
templates/
├── common/
│   ├── configs/          # Stack configs (settings.xml, .npmrc, etc.)
│   ├── build/           # Dockerfiles and .dockerignore
│   ├── gitignore/       # Stack-specific .gitignore files
│   └── README.md.j2     # Common README template
├── library/             # Library project templates
├── microservice/        # Microservice templates
├── monorepo/           # Monorepo templates with Helm charts
└── delivery/           # Delivery templates with Helm charts
```

## Architecture

```
FastAPI Routes → ProjectCreator → TemplateProcessor → S3 Templates
                      ↓               ↓
                 GitLabService → GitLab API (repos, files, variables)
```

## Development

### Project Structure

```
app/
├── api/routes.py           # FastAPI endpoints
├── core/config.py          # Settings and environment
├── schemas/repo_models.py  # Pydantic models
└── services/
    ├── gitlab_service.py   # GitLab API client
    ├── project_creator.py  # Main orchestration
    └── template_processor.py # S3 + Jinja2 processing
```

### Adding Features

**New Stack**: Add to `Stack` enum and create templates in S3
**New Project Type**: Add to model and create template directory
**New Template**: Upload to S3 with `.j2` suffix for processing

## License

MIT License
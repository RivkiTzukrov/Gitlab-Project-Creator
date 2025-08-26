# Final S3 Template Structure

## Overview
This structure provides complete project scaffolding with stack-specific base structures and project-type-specific configurations.

## S3 Directory Structure

```
s3://your-bucket/templates/
├── stacks/                           # Complete project structures per stack
│   ├── maven/                        # All files for Maven projects
│   │   ├── pom.xml.j2               # Maven project file
│   │   ├── settings.xml             # Maven config (static)
│   │   ├── .gitignore               # Maven gitignore (static)
│   │   ├── src/
│   │   │   ├── main/
│   │   │   │   ├── java/
│   │   │   │   │   └── com/
│   │   │   │   │       └── example/
│   │   │   │   │           └── Application.java.j2
│   │   │   │   └── resources/
│   │   │   │       └── application.yml.j2
│   │   │   └── test/
│   │   │       └── java/
│   │   │           └── com/
│   │   │               └── example/
│   │   │                   └── ApplicationTest.java.j2
│   │   └── ... (any other Maven-specific files)
│   │
│   ├── node/                         # All files for Node.js projects
│   │   ├── package.json.j2          # Node.js project file
│   │   ├── .npmrc                   # NPM config (static)
│   │   ├── .gitignore               # Node gitignore (static)
│   │   ├── src/
│   │   │   ├── index.js.j2          # Main entry point
│   │   │   └── routes/
│   │   │       └── health.js.j2     # Health check route
│   │   ├── test/
│   │   │   └── index.test.js.j2     # Basic test
│   │   └── ... (any other Node-specific files)
│   │
│   ├── python/                       # All files for Python projects
│   │   ├── pyproject.toml.j2        # Python project file
│   │   ├── requirements.txt.j2      # Dependencies
│   │   ├── pip.ini                  # Pip config (static)
│   │   ├── .gitignore               # Python gitignore (static)
│   │   ├── src/
│   │   │   └── {repo_name}/         # Package directory (dynamic name)
│   │   │       ├── __init__.py      # Empty file (static)
│   │   │       └── main.py.j2       # Main module
│   │   ├── tests/
│   │   │   ├── __init__.py          # Empty file (static)
│   │   │   └── test_main.py.j2      # Basic test
│   │   └── ... (any other Python-specific files)
│   │
│   └── dotnet/                       # All files for .NET projects
│       ├── {repo_name}.csproj.j2    # .NET project file (dynamic name)
│       ├── nuget.config             # NuGet config (static)
│       ├── .gitignore               # .NET gitignore (static)
│       ├── Program.cs.j2            # Main program
│       ├── Controllers/
│       │   └── HealthController.cs.j2 # Health endpoint
│       ├── Properties/
│       │   └── launchSettings.json.j2
│       ├── Tests/
│       │   ├── {repo_name}.Tests.csproj.j2
│       │   └── UnitTest1.cs.j2      # Basic test
│       └── ... (any other .NET-specific files)
│
├── docker/
│   ├── maven.Dockerfile
│   ├── node.Dockerfile
│   ├── python.Dockerfile
│   ├── dotnet.Dockerfile
│   └── .dockerignore
│
├── project-types/                    # Project type specific files
│   ├── library/                     # Library projects (no Docker/Helm)
│   │   ├── maven.gitlab-ci.yml.j2
│   │   ├── node.gitlab-ci.yml.j2
│   │   ├── python.gitlab-ci.yml.j2
│   │   └── dotnet.gitlab-ci.yml.j2
│   │
│   ├── microservice/                # Microservice projects (with Docker)
│   │   ├── maven.gitlab-ci.yml.j2
│   │   ├── node.gitlab-ci.yml.j2
│   │   ├── python.gitlab-ci.yml.j2
│   │   └── dotnet.gitlab-ci.yml.j2
│   │
│   ├── monorepo/                    # Monorepo projects (with Docker + Helm)
│   │   ├── maven.gitlab-ci.yml.j2
│   │   ├── node.gitlab-ci.yml.j2
│   │   ├── python.gitlab-ci.yml.j2
│   │   ├── dotnet.gitlab-ci.yml.j2
│   │   └── helm/
│   │       ├── Chart.yaml.j2
│   │       ├── values.yaml.j2
│   │       └── .helmignore
│   │
│   └── delivery/                    # Delivery projects (Helm only, no stack)
│       ├── .gitlab-ci.yml.j2
│       └── helm/
│           ├── Chart.yaml.j2
│           ├── values.yaml.j2
│           └── .helmignore
│
└── common/
    └── README.md.j2                 # Common README template
```

## File Processing Logic

### Template Files (.j2)
- Processed with Jinja2 using custom delimiters
- Variables: `{% repo_name %}`, `{% stack %}`, `{% project_type %}`
- Blocks: `{# if condition #}` ... `{# endif #}`

### Static Files
- Copied as-is without processing
- Config files, gitignore, dockerignore, etc.

### Dynamic Paths
- `{repo_name}` in paths gets replaced with actual repo name
- Example: `src/{repo_name}/` becomes `src/my-project/`

## Repository Generation Flow

1. **Stack Structure**: All files from `templates/stacks/{stack}/` are added
2. **Docker Files**: If microservice/monorepo, add from `templates/docker/{stack}/`
3. **CI/CD**: Add GitLab CI from `templates/project-types/{project_type}/`
4. **Helm**: If monorepo/delivery, add from `templates/project-types/{project_type}/helm/`
5. **README**: Add common README template

## Benefits

- **Complete Scaffolding**: Every repo gets full project structure
- **DRY Principle**: Dockerfiles shared across project types
- **Flexible**: Easy to add new stacks or project types
- **Discoverable**: Template processor auto-discovers files in S3
- **Maintainable**: Clear separation of concerns
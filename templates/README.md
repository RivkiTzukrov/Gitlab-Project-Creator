# GitLab Repository Templates

Template collection for GitLab Repository Sculptor - automatically synced to S3 bucket.

## Structure

```
templates/
├── common/
│   ├── configs/          # Stack-specific configs (settings.xml, .npmrc, pip.ini, nuget.config)
│   ├── build/           
│   │   ├── Dockerfiles/ # Stack-specific Dockerfiles
│   │   └── .dockerignore
│   ├── gitignore/       # Stack-specific .gitignore files
│   ├── .helmignore      # Helm ignore file
│   └── README.md.j2     # Common README template
├── library/
│   ├── maven.gitlab-ci.yml
│   ├── node.gitlab-ci.yml
│   ├── python.gitlab-ci.yml
│   └── dotnet.gitlab-ci.yml
├── microservice/
│   ├── maven.gitlab-ci.yml
│   ├── node.gitlab-ci.yml
│   ├── python.gitlab-ci.yml
│   └── dotnet.gitlab-ci.yml
├── monorepo/
│   ├── maven.gitlab-ci.yml
│   ├── node.gitlab-ci.yml
│   ├── python.gitlab-ci.yml
│   ├── dotnet.gitlab-ci.yml
│   └── helm/
│       ├── Chart.yaml.j2
│       ├── values.yaml.j2
│       └── .helmignore (copied from common/)
└── delivery/
    ├── .gitlab-ci.yml
    └── helm/
        ├── Chart.yaml.j2
        ├── values.yaml.j2
        └── .helmignore (copied from common/)
```

## Template Syntax

**Jinja2 Variables**: `{% variable_name %}`
**Jinja2 Blocks**: `{# if condition #}...{# endif #}`
**Helm Variables**: `{{ .Values.name }}` (unchanged)

### Available Variables

- `{% repo_name %}` - Sanitized repository name (lowercase, hyphens)
- `{% stack %}` - Technology stack (maven, node, python, dotnet)
- `{% project_type %}` - Project type (library, microservice, monorepo, delivery)

## File Processing

**Processed with Jinja2** (`.j2` suffix):
- `README.md.j2`
- `Chart.yaml.j2`
- `values.yaml.j2`
- All `.gitlab-ci.yml` files

**Copied as-is** (no processing):
- Dockerfiles
- `.gitignore` files
- `.dockerignore`
- `.helmignore`
- Config files (settings.xml, .npmrc, etc.)

## Adding Templates

1. **Create/edit template files** with `.j2` suffix for Jinja2 processing
2. **Use custom delimiters** to avoid conflicts with Helm syntax
3. **Commit changes** - CI will automatically sync to S3
4. **Test** with Repository Sculptor service

## CI/CD

Templates are automatically synced to S3 bucket on every commit to main branch.
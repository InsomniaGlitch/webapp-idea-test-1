## AudioWeb

Django audio archive application. The project uses PostgreSQL through environment-configured settings and is designed for containerized deployment behind a reverse proxy.

### Secrets handling

This project already uses Django’s standard pattern of reading secrets from process environment variables, with an optional local `.env` loader for development only. That is appropriate for this webapp because the only real secrets in scope are:

- `DJANGO_SECRET_KEY`
- `POSTGRES_PASSWORD`
- deployment-specific `SITE_URL`, email, and host allowlist values

A dedicated secrets manager such as AWS Secrets Manager, Azure Key Vault, GCP Secret Manager, or HashiCorp Vault is only recommended when the app is deployed to a managed hosting platform with centralized secret rotation and access control. For this local/standalone project, keeping secrets in `.env` (ignored by Git) and exporting them into the process environment is the modern, reliable approach.

```powershell
python manage.py check
python manage.py migrate
python manage.py test
```

Use `.env.example` as the configuration reference. Do not commit secrets, database files, media, Python caches, or local backups.

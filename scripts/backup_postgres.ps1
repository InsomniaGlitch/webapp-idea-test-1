param(
    [string]$BackupDirectory = "backups"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $BackupDirectory | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $BackupDirectory "audioweb-$timestamp.dump"

& pg_dump --format=custom --no-owner --no-acl --dbname="host=$env:POSTGRES_HOST port=$env:POSTGRES_PORT dbname=$env:POSTGRES_DB user=$env:POSTGRES_USER" --file=$backupPath
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed with exit code $LASTEXITCODE" }
Write-Output "Created $backupPath"

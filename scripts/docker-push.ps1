# Build and push all custom images to Docker Hub.
#
# Usage:
#   $env:DOCKERHUB_USER = "yourusername"
#   $env:IMAGE_TAG = "latest"          # optional
#   $env:DEPLOY_HOST = "your.server"   # baked into frontend API URLs at build time
#   .\scripts\docker-push.ps1
#
# Prerequisite: docker login

param(
    [string]$DockerHubUser = $env:DOCKERHUB_USER,
    [string]$Tag = $(if ($env:IMAGE_TAG) { $env:IMAGE_TAG } else { "latest" }),
    [string]$DeployHost = $(if ($env:DEPLOY_HOST) { $env:DEPLOY_HOST } else { "localhost" })
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (-not $DockerHubUser) {
    Write-Error "Set DOCKERHUB_USER or pass -DockerHubUser. Example: `$env:DOCKERHUB_USER='sidonweb'"
}

function Build-And-Push {
    param(
        [string]$Name,
        [string]$Context,
        [string[]]$BuildArgs = @()
    )

    $image = "${DockerHubUser}/${Name}:${Tag}"
    Write-Host "`n=== Building $image ===" -ForegroundColor Cyan

    $buildCmd = @("build", "-t", $image)
    foreach ($arg in $BuildArgs) { $buildCmd += @("--build-arg", $arg) }
    $buildCmd += $Context

    & docker @buildCmd
    if ($LASTEXITCODE -ne 0) { throw "docker build failed for $Name" }

    Write-Host "=== Pushing $image ===" -ForegroundColor Cyan
    & docker push $image
    if ($LASTEXITCODE -ne 0) { throw "docker push failed for $Name (run 'docker login' first)" }

    Write-Host "Pushed $image" -ForegroundColor Green
}

Write-Host "Registry : docker.io/$DockerHubUser" -ForegroundColor Yellow
Write-Host "Tag      : $Tag" -ForegroundColor Yellow
Write-Host "Deploy host (frontend API URLs): $DeployHost" -ForegroundColor Yellow

Build-And-Push -Name "bitheads-ecom-backend" -Context "$Root/packages/ecom-backend"

Build-And-Push -Name "bitheads-copilot-backend" -Context "$Root/packages/copilot-backend"

Build-And-Push -Name "bitheads-playwright-mcp" -Context "$Root/packages/playwright-mcp" `
    -BuildArgs @("PLAYWRIGHT_LOCALHOST_ALIAS=$DeployHost")

Build-And-Push -Name "bitheads-ecom-web" -Context "$Root/packages/ecom" `
    -BuildArgs @("VITE_API_BASE=http://${DeployHost}:3002")

Build-And-Push -Name "bitheads-dashboard" -Context "$Root/packages/dashboard" `
    -BuildArgs @(
        "VITE_API_BASE=http://${DeployHost}:3001",
        "VITE_ECOM_API_BASE=http://${DeployHost}:3002",
        "VITE_DEMO_MODE=true"
    )

Write-Host "`nAll images pushed to docker.io/$DockerHubUser" -ForegroundColor Green
Write-Host "Deploy with: docker compose -f docker-compose.prod.yml up -d" -ForegroundColor Green

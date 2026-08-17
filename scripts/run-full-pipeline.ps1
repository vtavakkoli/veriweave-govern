$ErrorActionPreference = "Stop"

$pipelineExit = 0

try {
    docker compose --profile pipeline down --volumes --remove-orphans

    docker compose --profile pipeline up `
        --build `
        --abort-on-container-exit `
        --exit-code-from pipeline `
        pipeline

    $pipelineExit = $LASTEXITCODE
    if ($pipelineExit -ne 0) {
        throw "Full publication pipeline failed with exit code $pipelineExit."
    }

    Write-Host "`nFull publication pipeline completed successfully." -ForegroundColor Green
    Write-Host "Summary: .\results\pipeline-summary.json" -ForegroundColor Cyan
}
catch {
    if ($pipelineExit -eq 0) {
        $pipelineExit = 1
    }
    Write-Error $_
}
finally {
    Write-Host "`nStopping and removing pipeline containers..." -ForegroundColor Yellow
    docker compose --profile pipeline down --volumes --remove-orphans
}

exit $pipelineExit

param(
    [string]$OutDir = "data/external/wemac"
)

$ErrorActionPreference = "Stop"

$datasets = @(
    @{ Name = "physiological_signals"; Doi = "doi:10.21950/FNUHKE" },
    @{ Name = "audio_features"; Doi = "doi:10.21950/XKHCCW" },
    @{ Name = "emotional_labelling"; Doi = "doi:10.21950/RYUCLV" },
    @{ Name = "questionnaire"; Doi = "doi:10.21950/U5DXJR" }
)

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$summary = @()

foreach ($dataset in $datasets) {
    $name = $dataset.Name
    $doi = $dataset.Doi
    $datasetDir = Join-Path $OutDir $name
    New-Item -ItemType Directory -Force -Path $datasetDir | Out-Null

    $encodedDoi = [System.Uri]::EscapeDataString($doi)
    $apiUrl = "https://edatos.consorciomadrono.es/api/datasets/:persistentId/?persistentId=$encodedDoi"
    Write-Host "Fetching metadata: $name ($doi)"
    $metadata = Invoke-RestMethod -Uri $apiUrl -Method Get

    $metadataPath = Join-Path $datasetDir "dataverse_metadata.json"
    $metadata | ConvertTo-Json -Depth 100 | Set-Content -Path $metadataPath -Encoding UTF8

    $files = $metadata.data.latestVersion.files
    foreach ($file in $files) {
        $fileId = $file.dataFile.id
        $fileName = $file.dataFile.filename
        $target = Join-Path $datasetDir $fileName

        $status = "downloaded"
        $errorMessage = ""

        if (Test-Path $target) {
            Write-Host "Already exists: $target"
            $status = "already_exists"
        } else {
            $downloadUrl = "https://edatos.consorciomadrono.es/api/access/datafile/$fileId"
            Write-Host "Downloading: $fileName"
            try {
                Invoke-WebRequest -Uri $downloadUrl -OutFile $target
            } catch {
                $status = "blocked_or_failed"
                $errorMessage = $_.Exception.Message
                Write-Warning "Could not download ${fileName}: $errorMessage"
            }
        }

        $summary += [pscustomobject]@{
            dataset = $name
            doi = $doi
            file_id = $fileId
            file_name = $fileName
            path = $target
            status = $status
            error = $errorMessage
            encrypted_note = $file.dataFile.description
            filesize = $file.dataFile.filesize
        }
    }
}

$summaryPath = Join-Path $OutDir "wemac_download_manifest.csv"
$summary | Export-Csv -Path $summaryPath -NoTypeInformation -Encoding UTF8
Write-Host "Wrote manifest: $summaryPath"

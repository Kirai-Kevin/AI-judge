Write-Host "Testing AI-Judge API Endpoints" -ForegroundColor Green

# Function to make HTTP requests
function Invoke-APIRequest {
    param (
        [string]$Method,
        [string]$Endpoint,
        [string]$Body = ""
    )
    
    $baseUrl = "http://127.0.0.1:5000"
    $url = "$baseUrl$Endpoint"
    
    Write-Host "`nTesting $Method $Endpoint" -ForegroundColor Cyan
    
    try {
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        if ($Body -eq "") {
            $response = Invoke-RestMethod -Method $Method -Uri $url -Headers $headers
        }
        else {
            $response = Invoke-RestMethod -Method $Method -Uri $url -Headers $headers -Body $Body
        }
        
        Write-Host "Response:" -ForegroundColor Green
        $response | ConvertTo-Json -Depth 10
    }
    catch {
        Write-Host "Error:" -ForegroundColor Red
        Write-Host $_.Exception.Message
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $reader.BaseStream.Position = 0
            $reader.DiscardBufferedData()
            $responseBody = $reader.ReadToEnd()
            Write-Host "Response body:" -ForegroundColor Red
            Write-Host $responseBody
        }
    }
}

# Test 1: Configure Questions
$configureQuestionsBody = @{
    categories = @(
        @{
            name = "Problem"
            weight = 0.10
            questions = @(
                @{
                    id = "prob_1"
                    text = "Is there a clear problem?"
                    weight = 0.25
                },
                @{
                    id = "prob_2"
                    text = "Is there evidence to support the importance of the problem?"
                    weight = 0.25
                },
                @{
                    id = "prob_3"
                    text = "Is the problem solvable?"
                    weight = 0.25
                },
                @{
                    id = "prob_4"
                    text = "How obsessed is the team on the problem?"
                    weight = 0.25
                }
            )
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-APIRequest -Method "POST" -Endpoint "/api/configure-questions" -Body $configureQuestionsBody

# Test 2: Submit Evaluation
$evaluationBody = @{
    startupId = "test_startup_1"
    evaluationConfig = @{
        categories = @(
            @{
                name = "Problem"
                weight = 0.10
                questions = @(
                    @{
                        id = "prob_1"
                        text = "Is there a clear problem?"
                        weight = 0.25
                    }
                )
            }
        )
    }
    evaluations = @(
        @{
            roundId = "round_1"
            responses = @(
                @{
                    questionId = "prob_1"
                    score = 9
                    feedback = "The problem is clearly articulated and well-defined"
                    skipped = $false
                }
            )
            roundFeedback = "Good understanding of the problem space"
        }
    )
    nominations = @{
        isNominated = $true
        willBeMentored = $false
        willBeMet = $true
    }
} | ConvertTo-Json -Depth 10

Invoke-APIRequest -Method "POST" -Endpoint "/rankings/generate" -Body $evaluationBody

# Test CSV download endpoint
Write-Host "`nTesting POST /rankings/download"
$downloadBody = @(
    @{
        startup_id = "test_startup_1"
        startup_name = "Test Startup"
        judges_feedback = @(
            @{
                judge_id = "judge_1"
                nominated_for_next_round = $true
                mentor_interest = $false
                hero_want_to_meet = $true
                responses = @(
                    @{
                        question_id = "prob_1"
                        score = 4
                        feedback = "Clear problem identified"
                    }
                    @{
                        question_id = "prob_2"
                        score = 5
                        feedback = "Strong evidence provided"
                    }
                )
            }
        )
    }
) | ConvertTo-Json -Depth 10

try {
    $downloadResponse = Invoke-RestMethod -Uri "http://127.0.0.1:5000/rankings/download" -Method Post -Body $downloadBody -ContentType "application/json" -OutFile "test_rankings.zip"
    Write-Host "Rankings file downloaded successfully as test_rankings.zip"
    
    # Test if the zip file exists and contains CSV files
    if (Test-Path "test_rankings.zip") {
        Write-Host "ZIP file created successfully"
        # Clean up
        Remove-Item "test_rankings.zip" -Force
    }
} catch {
    Write-Host "Error:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response body:"
        Write-Host $responseBody
    }
}

Write-Host "`nAll tests completed!" -ForegroundColor Green

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

# Test rankings generation endpoint
Write-Host "`nTesting POST /rankings/generate"
$generateBody = @(
    @{
        startupId = "test_startup_1"
        judgeId = "test_judge_1"
        averageScore = 8.5
        feedback = "Strong potential in innovation and market opportunity"
        individualScores = @(
            @{
                roundId = "round_1"
                average = 8.0
                criteria = @(
                    @{
                        score = 9
                        question = "Clear problem identification"
                        skipped = $false
                    }
                    @{
                        score = 8
                        question = "Solution coherence"
                        skipped = $false
                    }
                    @{
                        score = 7
                        question = "Market size assessment"
                        skipped = $false
                    }
                )
                feedback = "Good understanding of the market size."
            }
            @{
                roundId = "round_2"
                average = 9.0
                criteria = @(
                    @{
                        score = 9
                        question = "Revenue model viability"
                        skipped = $false
                    }
                    @{
                        score = 8
                        question = "Technical implementation viability"
                        skipped = $false
                    }
                )
                feedback = "Strong revenue model and technical implementation."
            }
        )
        isNominated = $true
        willBeMentored = $false
        willBeMet = $true
    }
    @{
        startupId = "test_startup_2"
        judgeId = "test_judge_2"
        averageScore = 7.5
        feedback = "Innovative solution but needs market validation"
        individualScores = @(
            @{
                roundId = "round_1"
                average = 7.0
                criteria = @(
                    @{
                        score = 8
                        question = "Clear problem identification"
                        skipped = $false
                    }
                    @{
                        score = 7
                        question = "Solution coherence"
                        skipped = $false
                    }
                    @{
                        score = 6
                        question = "Market size assessment"
                        skipped = $false
                    }
                )
                feedback = "Problem is well-defined but market size needs validation."
            }
            @{
                roundId = "round_2"
                average = 8.0
                criteria = @(
                    @{
                        score = 8
                        question = "Revenue model viability"
                        skipped = $false
                    }
                    @{
                        score = 7
                        question = "Technical implementation viability"
                        skipped = $false
                    }
                )
                feedback = "Revenue model is promising but technical implementation needs refinement."
            }
        )
        isNominated = $false
        willBeMentored = $true
        willBeMet = $false
    }
) | ConvertTo-Json -Depth 10

try {
    $generateResponse = Invoke-RestMethod -Uri "http://127.0.0.1:5000/rankings/generate" -Method Post -Body $generateBody -ContentType "application/json"
    Write-Host "Response:"
    $generateResponse | ConvertTo-Json
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

# Test CSV download endpoint
Write-Host "`nTesting POST /rankings/download"
$downloadBody = @(
    @{
        startupId = "test_startup_1"
        judgeId = "test_judge_1"
        averageScore = 8.5
        feedback = "Strong potential in innovation and market opportunity"
        individualScores = @(
            @{
                roundId = "round_1"
                average = 8.0
                criteria = @(
                    @{
                        score = 9
                        question = "Clear problem identification"
                        skipped = $false
                    }
                    @{
                        score = 8
                        question = "Solution coherence"
                        skipped = $false
                    }
                    @{
                        score = 7
                        question = "Market size assessment"
                        skipped = $false
                    }
                )
                feedback = "Good understanding of the market size."
            }
            @{
                roundId = "round_2"
                average = 9.0
                criteria = @(
                    @{
                        score = 9
                        question = "Revenue model viability"
                        skipped = $false
                    }
                    @{
                        score = 8
                        question = "Technical implementation viability"
                        skipped = $false
                    }
                )
                feedback = "Strong revenue model and technical implementation."
            }
        )
        isNominated = $true
        willBeMentored = $false
        willBeMet = $true
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

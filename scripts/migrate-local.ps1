param(
    [string]$Psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe",
    [string]$DbHost = "localhost",
    [int]$Port = 5432,
    [string]$User = "postgres",
    [string]$CustomerDatabase = "veripay_customer_db",
    [string]$BankDatabase = "veripay_bank_db",
    [string]$FraudOperationsDatabase = "veripay_fraud_ops_db",
    [string]$MerchantDatabase = "veripay_merchant_db",
    [string]$MobileDatabase = "veripay_mobile_db"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $Psql)) {
    throw "psql was not found at '$Psql'. Pass the installed path with -Psql."
}

$root = Split-Path -Parent $PSScriptRoot
$migrations = @(
    @{ Database = $CustomerDatabase; File = Join-Path $root "datasets\migrations\customer\001_customer.sql" },
    @{ Database = $BankDatabase; File = Join-Path $root "datasets\migrations\bank\001_bank.sql" },
    @{ Database = $FraudOperationsDatabase; File = Join-Path $root "datasets\migrations\fraud_ops\001_fraud_operations.sql" },
    @{ Database = $MerchantDatabase; File = Join-Path $root "datasets\migrations\merchant\001_merchant.sql" },
    @{ Database = $MobileDatabase; File = Join-Path $root "datasets\migrations\mobile\001_mobile.sql" }
)

foreach ($migration in $migrations) {
    if (-not (Test-Path $migration.File)) {
        throw "Migration file was not found: $($migration.File)"
    }

    Write-Host "Applying $($migration.File) to $($migration.Database)..."
    & $Psql -h $DbHost -p $Port -U $User -d $migration.Database `
        --set ON_ERROR_STOP=on -f $migration.File
    if ($LASTEXITCODE -ne 0) {
        throw "Migration failed for database '$($migration.Database)'."
    }
}

Write-Host "All VeriPay domain migrations completed."

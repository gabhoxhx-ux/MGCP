# Bootstrap unificado: crea virtualenv, instala dependencias, configura BD y lanza la webapp
# Uso: powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1

Write-Host ""; Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "        MGCP - Bootstrap (Instalar + Configurar + Iniciar)   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan; Write-Host ""

# 1) Verificar Python
Write-Host "🔍 Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Python no encontrado. Instale Python 3.10+" -ForegroundColor Red; exit 1 }
Write-Host "✅ $pythonVersion encontrado" -ForegroundColor Green; Write-Host ""

# 2) Directorio del script
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
Write-Host "📂 Directorio de trabajo: $scriptPath" -ForegroundColor Cyan; Write-Host ""

# 3) Crear virtualenv (./.venv) y activar
Write-Host "📦 Preparando entorno virtual (.venv)..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
	python -m venv .venv
}
& ".venv\\Scripts\\Activate.ps1"
if ($null -eq $env:VIRTUAL_ENV) { Write-Host "❌ No se pudo activar el virtualenv" -ForegroundColor Red; exit 1 }
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Error instalando dependencias" -ForegroundColor Red; exit 1 }
Write-Host "✅ Entorno virtual y dependencias listos" -ForegroundColor Green; Write-Host ""

# 4) Directorios requeridos
$directories = @("database","documentos_generados","app\\static\\images","app\\templates\\pdf")
foreach ($dir in $directories) { if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null; Write-Host "   ✅ Creado: $dir" -ForegroundColor Green } }
Write-Host ""; Write-Host "✅ Directorios listos" -ForegroundColor Green; Write-Host ""

# 5) Configurar variables de entorno mínimas (admin)
Write-Host "🔐 Configurando credenciales de administrador..." -ForegroundColor Yellow
if (-not $env:ADMIN_USER) { $env:ADMIN_USER = "admin" }
if (-not $env:ADMIN_PASS) { $env:ADMIN_PASS = "admin123" }
Write-Host "   Usuario: $($env:ADMIN_USER)" -ForegroundColor Gray
Write-Host "   Clave:   $($env:ADMIN_PASS)" -ForegroundColor Gray

# 6) Configurar sistema (tablas + datos + propuestas)
Write-Host "⚙️ Configurando sistema..." -ForegroundColor Yellow
python .\configurar_sistema.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Error configurando el sistema" -ForegroundColor Red; exit 1 }
Write-Host "✅ Configuración completada" -ForegroundColor Green; Write-Host ""

# 7) Verificar
Write-Host "🔎 Verificando instalación..." -ForegroundColor Yellow
python .\verificar_sistema.py
if ($LASTEXITCODE -ne 0) { Write-Host "⚠️ Verificación con observaciones. Continuando con inicio." -ForegroundColor Yellow }
else { Write-Host "✅ Verificación OK" -ForegroundColor Green }

# 8) Lanzar webapp
Write-Host "\n🚀 Iniciando webapp MGCP en http://localhost:5000 ..." -ForegroundColor Green
python .\run.py

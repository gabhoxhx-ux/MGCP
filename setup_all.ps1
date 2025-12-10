# Instalador unificado de MGCP (Windows PowerShell)
# Ejecutar: powershell -ExecutionPolicy Bypass -File .\setup_all.ps1

Write-Host ""; Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "           MGCP - Instalación y Configuración Unificada      " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan; Write-Host ""

# 1) Verificar Python
Write-Host "🔍 Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Python no encontrado. Instale Python 3.10+" -ForegroundColor Red; exit 1 }
Write-Host "✅ $pythonVersion encontrado" -ForegroundColor Green; Write-Host ""

# 2) Ubicarse en el directorio del script
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
Write-Host "📂 Directorio de trabajo: $scriptPath" -ForegroundColor Cyan; Write-Host ""

# 3) Instalar dependencias
Write-Host "📦 Instalando dependencias (requirements.txt)..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Error instalando dependencias" -ForegroundColor Red; exit 1 }
Write-Host "✅ Dependencias instaladas" -ForegroundColor Green; Write-Host ""

# 4) Crear estructura de directorios
Write-Host "📁 Verificando/creando directorios..." -ForegroundColor Yellow
$directories = @("database","documentos_generados","app\\static\\images","app\\templates\\pdf")
foreach ($dir in $directories) {
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null; Write-Host "   ✅ Creado: $dir" -ForegroundColor Green }
  else { Write-Host "   ℹ️  Ya existe: $dir" -ForegroundColor Gray }
}
Write-Host ""; Write-Host "✅ Directorios listos" -ForegroundColor Green; Write-Host ""

# 5) Configurar Base de Datos + Datos + Propuestas
Write-Host "⚙️ Ejecutando configuración del sistema (tablas, clientes, propuestas)..." -ForegroundColor Yellow
python .\configurar_sistema.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Error configurando el sistema" -ForegroundColor Red; exit 1 }
Write-Host "✅ Configuración de BD y datos completada" -ForegroundColor Green; Write-Host ""

# 6) Verificación integral
Write-Host "🔎 Ejecutando verificación del sistema..." -ForegroundColor Yellow
python .\verificar_sistema.py
if ($LASTEXITCODE -ne 0) { Write-Host "⚠️ Verificación reportó pendientes. Revise mensajes anteriores." -ForegroundColor Yellow }
else { Write-Host "✅ Verificación OK" -ForegroundColor Green }
Write-Host ""

# 7) Resumen y opción de inicio
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                 ✅ INSTALACIÓN COMPLETADA                 " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""; Write-Host "🚀 Para iniciar el sistema:" -ForegroundColor Yellow
Write-Host "   python run.py" -ForegroundColor White
Write-Host ""; Write-Host "🌐 Acceso:" -ForegroundColor Yellow
Write-Host "   http://localhost:5000" -ForegroundColor White
Write-Host ""; 
$respuesta = Read-Host "¿Desea iniciar el sistema ahora? (S/N)"
if ($respuesta -eq "S" -or $respuesta -eq "s") { Write-Host "\n🚀 Iniciando MGCP..." -ForegroundColor Green; python run.py }
else { Write-Host "\n👍 Sistema listo. Ejecute 'python run.py' cuando desee iniciar." -ForegroundColor Cyan }

"""
Script de verificación del sistema MGCP
Valida que todos los componentes estén correctos
"""
import os
import sys

def verificar_estructura():
    """Verifica que existan todos los archivos necesarios"""
    print("="*70)
    print("[*] VERIFICACION DEL SISTEMA MGCP")
    print("="*70)
    print()
    
    archivos_requeridos = [
        # Scripts Python
        ('run.py', '🐍 Script principal'),
        ('configurar_sistema.py', '⚙️ Configurador'),
        ('generar_propuestas.py', '📋 Generador propuestas'),
        ('inicializar_clientes.py', '👥 Inicializador clientes'),
        
        # Módulo app
        ('app/__init__.py', '📦 Inicialización app'),
        ('app/models.py', '🗄️ Modelos BD'),
        ('app/routes.py', '🛣️ Rutas sistema'),
        
        # Templates principales
        ('app/templates/base.html', '📄 Template base'),
        ('app/templates/dashboard.html', '📊 Dashboard'),
        ('app/templates/portal_cliente.html', '👤 Portal cliente'),
        ('app/templates/detalle_propuesta.html', '📝 Detalle propuesta'),
        ('app/templates/pdf/contrato_template.html', '📜 Template contrato'),
        
        # Configuración
        ('requirements.txt', '📋 Dependencias'),
        
        # Documentación
        ('README_NUEVO.md', '📚 README principal'),
        ('GUIA_INICIO_RAPIDO.md', '🚀 Guía inicio'),
        ('RESUMEN_EJECUTIVO_FINAL.md', '📊 Resumen ejecutivo'),
        ('RESUMEN_VISUAL_COMPLETO.md', '🎨 Resumen visual'),
        ('GUIA_PRUEBAS.md', '🧪 Guía pruebas'),
        ('INDICE_DOCUMENTACION.md', '📚 Índice'),
    ]
    
    archivos_encontrados = 0
    archivos_faltantes = []
    
    print("📁 Verificando archivos del sistema...")
    print()
    
    for archivo, descripcion in archivos_requeridos:
        ruta_completa = os.path.join(os.path.dirname(__file__), archivo)
        existe = os.path.exists(ruta_completa)
        
        if existe:
            print(f"[+] {descripcion}: {archivo}")
            archivos_encontrados += 1
        else:
            print(f"[-] {descripcion}: {archivo} - NO ENCONTRADO")
            archivos_faltantes.append(archivo)
    
    print()
    print("="*70)
    print(f"Archivos encontrados: {archivos_encontrados}/{len(archivos_requeridos)}")
    
    if archivos_faltantes:
        print()
        print("[!] ADVERTENCIA: Archivos faltantes:")
        for archivo in archivos_faltantes:
            print(f"   - {archivo}")
        return False
    
    print("[+] Todos los archivos necesarios estan presentes")
    return True

def verificar_base_datos():
    """Verifica la base de datos"""
    print()
    print("="*70)
    print("[*] Verificando base de datos...")
    print()
    
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'mgcp.db')
    
    if not os.path.exists(db_path):
        print("[-] Base de datos no encontrada")
        print("   Ejecute: python configurar_sistema.py")
        return False
    
    print(f"[+] Base de datos encontrada: {db_path}")
    
    # Intentar conectar y contar registros
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from app import app, db
        from app.models import Cliente, Propuesta, DocumentoGenerado
        
        with app.app_context():
            clientes = Cliente.query.count()
            propuestas = Propuesta.query.count()
            documentos = DocumentoGenerado.query.count()
            
            print()
            print("[*] Estadisticas de la base de datos:")
            print(f"   [i] Clientes: {clientes}")
            print(f"   [i] Propuestas: {propuestas}")
            print(f"   [i] Documentos: {documentos}")
            
            if clientes == 0:
                print()
                print("[!] No hay clientes en el sistema")
                print("   Ejecute: python inicializar_clientes.py")
                return False
            
            if propuestas == 0:
                print()
                print("[!] No hay propuestas en el sistema")
                print("   Ejecute: python generar_propuestas.py")
                return False
            
            print()
            print("[+] Base de datos con datos correctos")
            return True
            
    except Exception as e:
        print(f"[-] Error al verificar base de datos: {e}")
        return False

def verificar_dependencias():
    """Verifica las dependencias de Python"""
    print()
    print("="*70)
    print("[*] Verificando dependencias de Python...")
    print()
    
    dependencias = [
        'flask',
        'flask_sqlalchemy',
        'werkzeug',
    ]
    
    dependencias_ok = True
    
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"[+] {dep}")
        except ImportError:
            print(f"[-] {dep} - NO INSTALADO")
            dependencias_ok = False
    
    if not dependencias_ok:
        print()
        print("[!] Instale las dependencias:")
        print("   pip install -r requirements.txt")
        return False
    
    print()
    print("[+] Todas las dependencias instaladas")
    return True

def verificar_directorios():
    """Verifica que existan los directorios necesarios"""
    print()
    print("="*70)
    print("[*] Verificando estructura de directorios...")
    print()
    
    directorios = [
        'app',
        'app/templates',
        'app/templates/pdf',
        'app/static',
        'app/static/css',
        'app/static/js',
        'database',
        'documentos_generados',
    ]
    
    for directorio in directorios:
        ruta = os.path.join(os.path.dirname(__file__), directorio)
        if os.path.exists(ruta):
            print(f"[+] {directorio}/")
        else:
            print(f"[!] {directorio}/ - Creando...")
            os.makedirs(ruta, exist_ok=True)
    
    print()
    print("[+] Estructura de directorios correcta")
    return True

def main():
    """Ejecuta todas las verificaciones"""
    
    # Verificar estructura de archivos
    archivos_ok = verificar_estructura()
    
    # Verificar directorios
    directorios_ok = verificar_directorios()
    
    # Verificar dependencias
    dependencias_ok = verificar_dependencias()
    
    # Verificar base de datos
    bd_ok = verificar_base_datos()
    
    # Resumen final
    print()
    print("="*70)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("="*70)
    print()
    print(f"{'✅' if archivos_ok else '❌'} Archivos del sistema")
    print(f"{'✅' if directorios_ok else '❌'} Estructura de directorios")
    print(f"{'✅' if dependencias_ok else '❌'} Dependencias Python")
    print(f"{'✅' if bd_ok else '❌'} Base de datos")
    print()
    
    if all([archivos_ok, directorios_ok, dependencias_ok, bd_ok]):
        print("="*70)
        print("✅ SISTEMA COMPLETAMENTE FUNCIONAL")
        print("="*70)
        print()
        print("🚀 Puede iniciar el sistema con:")
        print("   python run.py")
        print()
        print("🌐 Acceder en:")
        print("   http://localhost:5000")
        print()
        return True
    else:
        print("="*70)
        print("⚠️ SISTEMA REQUIERE CONFIGURACIÓN")
        print("="*70)
        print()
        print("Ejecute los siguientes comandos:")
        if not dependencias_ok:
            print("   pip install -r requirements.txt")
        if not bd_ok:
            print("   python configurar_sistema.py")
        print()
        return False

if __name__ == "__main__":
    resultado = main()
    sys.exit(0 if resultado else 1)

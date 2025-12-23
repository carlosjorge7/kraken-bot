#!/usr/bin/env python3
"""
Script de Verificación del Sistema

Este script verifica que todos los componentes del bot estén
correctamente instalados y funcionando.

Uso:
    python verificar_sistema.py
"""

import sys
import os


def check_python_version():
    """Verifica la versión de Python."""
    print("🐍 Verificando versión de Python...")
    version = sys.version_info
    
    if version.major >= 3 and version.minor >= 10:
        print(f"   ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ✗ Python {version.major}.{version.minor}.{version.micro}")
        print(f"   ⚠️ Se requiere Python 3.10 o superior")
        return False


def check_dependencies():
    """Verifica que las dependencias estén instaladas."""
    print("\n📦 Verificando dependencias...")
    
    required = {
        'ccxt': 'Librería para acceso a exchanges',
        'pandas': 'Análisis de datos',
        'yaml': 'Lectura de configuración',
    }
    
    all_ok = True
    
    for module, description in required.items():
        try:
            if module == 'yaml':
                import yaml
            else:
                __import__(module)
            print(f"   ✓ {module:15} - {description}")
        except ImportError:
            print(f"   ✗ {module:15} - {description} [FALTA]")
            all_ok = False
    
    return all_ok


def check_project_structure():
    """Verifica la estructura de archivos del proyecto."""
    print("\n📁 Verificando estructura del proyecto...")
    
    required_files = [
        'main.py',
        'config/settings.yaml',
        'fetcher/__init__.py',
        'fetcher/kraken_client.py',
        'core/__init__.py',
        'core/engine.py',
        'indicators/__init__.py',
        'indicators/rsi.py',
        'alerts/__init__.py',
        'alerts/telegram.py',
    ]
    
    required_dirs = [
        'config',
        'fetcher',
        'core',
        'indicators',
        'alerts',
        'logs',
        'data',
    ]
    
    all_ok = True
    
    # Verificar directorios
    for directory in required_dirs:
        if os.path.isdir(directory):
            print(f"   ✓ Directorio: {directory}/")
        else:
            print(f"   ✗ Directorio: {directory}/ [FALTA]")
            all_ok = False
    
    # Verificar archivos
    for file_path in required_files:
        if os.path.isfile(file_path):
            print(f"   ✓ Archivo: {file_path}")
        else:
            print(f"   ✗ Archivo: {file_path} [FALTA]")
            all_ok = False
    
    return all_ok


def check_config():
    """Verifica que la configuración sea válida."""
    print("\n⚙️ Verificando configuración...")
    
    try:
        import yaml
        
        with open('config/settings.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Verificar secciones principales
        required_sections = ['exchange', 'database', 'logging', 'indicators', 'alerts']
        
        all_ok = True
        for section in required_sections:
            if section in config:
                print(f"   ✓ Sección: {section}")
            else:
                print(f"   ✗ Sección: {section} [FALTA]")
                all_ok = False
        
        # Verificar configuración del exchange
        if 'exchange' in config:
            symbol = config['exchange'].get('symbol', 'N/A')
            timeframe = config['exchange'].get('timeframe', 'N/A')
            print(f"   • Par configurado: {symbol}")
            print(f"   • Timeframe: {timeframe}")
        
        return all_ok
        
    except Exception as e:
        print(f"   ✗ Error al leer configuración: {e}")
        return False


def check_kraken_connection():
    """Verifica la conexión con Kraken."""
    print("\n🌐 Verificando conexión con Kraken...")
    
    try:
        from fetcher import KrakenClient
        
        client = KrakenClient()
        
        # Intentar conexión
        if client.check_connection():
            print("   ✓ Conexión con Kraken exitosa")
            
            # Obtener info del exchange
            info = client.get_exchange_info()
            print(f"   • Exchange: {info.get('name', 'N/A')}")
            print(f"   • OHLCV disponible: {info.get('has', {}).get('fetchOHLCV', False)}")
            
            return True
        else:
            print("   ✗ No se pudo conectar con Kraken")
            return False
            
    except Exception as e:
        print(f"   ✗ Error al conectar: {e}")
        return False


def check_indicators():
    """Verifica que los indicadores funcionen."""
    print("\n📊 Verificando indicadores...")
    
    try:
        import pandas as pd
        from indicators import calculate_rsi
        
        # Crear datos de prueba
        test_data = pd.DataFrame({
            'close': [100 + i for i in range(20)]
        })
        
        # Calcular RSI
        result = calculate_rsi(test_data, period=14)
        
        if 'rsi' in result.columns:
            print("   ✓ RSI: Funcionando correctamente")
            return True
        else:
            print("   ✗ RSI: No se calculó correctamente")
            return False
            
    except Exception as e:
        print(f"   ✗ Error al verificar indicadores: {e}")
        return False


def main():
    """Función principal de verificación."""
    print("=" * 70)
    print("  VERIFICACIÓN DEL SISTEMA - KRAKEN BOT")
    print("=" * 70)
    
    checks = [
        ("Python", check_python_version),
        ("Dependencias", check_dependencies),
        ("Estructura", check_project_structure),
        ("Configuración", check_config),
        ("Conexión Kraken", check_kraken_connection),
        ("Indicadores", check_indicators),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error en {name}: {e}")
            results.append((name, False))
    
    # Resumen
    print("\n" + "=" * 70)
    print("  RESUMEN DE VERIFICACIÓN")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ OK" if result else "❌ FALLÓ"
        print(f"  {status:10} - {name}")
    
    print(f"\n  Total: {passed}/{total} verificaciones pasadas")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ¡Sistema completamente funcional!")
        print("   Puedes ejecutar: python main.py")
        print()
        return 0
    else:
        print("\n⚠️ Hay problemas que necesitan ser resueltos.")
        print("   Revisa los errores anteriores.")
        print()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Verificación interrumpida\n")
        sys.exit(130)

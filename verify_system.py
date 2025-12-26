#!/usr/bin/env python3
"""
Script de Verificación - Sistema de Predicción Profesional

Verifica que todos los componentes estén correctamente instalados.
"""

import sys
from pathlib import Path


def check_file(filepath: str, min_lines: int = 0) -> bool:
    """Verifica que un archivo exista y tenga contenido"""
    path = Path(filepath)
    if not path.exists():
        print(f"❌ {filepath} - NO EXISTE")
        return False
    
    if min_lines > 0:
        lines = len(path.read_text().splitlines())
        if lines < min_lines:
            print(f"⚠️  {filepath} - Solo {lines} líneas (esperadas {min_lines}+)")
            return False
    
    print(f"✅ {filepath}")
    return True


def check_import(module: str) -> bool:
    """Verifica que un módulo se pueda importar"""
    try:
        __import__(module)
        print(f"✅ import {module}")
        return True
    except Exception as e:
        print(f"❌ import {module} - {e}")
        return False


def main():
    print("🔍 VERIFICACIÓN DEL SISTEMA\n")
    
    checks = []
    
    # Archivos core
    print("📦 ARCHIVOS CORE:")
    checks.append(check_file("analytics/__init__.py"))
    checks.append(check_file("analytics/backtester.py", 300))
    checks.append(check_file("predictive/enhanced_predictor.py", 300))
    
    print("\n📦 ARCHIVOS MODIFICADOS:")
    checks.append(check_file("core/engine.py", 200))
    checks.append(check_file("config/settings.yaml", 50))
    checks.append(check_file("backend/app/models/schemas.py", 200))
    checks.append(check_file("backend/app/api/routes.py", 250))
    checks.append(check_file("backend/app/services/state_reader.py", 400))
    
    print("\n📦 IMPORTS:")
    checks.append(check_import("analytics.backtester"))
    checks.append(check_import("predictive.enhanced_predictor"))
    
    # Resumen
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n{'='*60}")
    print(f"RESULTADO: {passed}/{total} checks passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("✅ SISTEMA COMPLETAMENTE VERIFICADO")
        print("\n📋 PRÓXIMOS PASOS:")
        print("  1. Ejecutar main.py para acumular predicciones")
        print("  2. Esperar 1-3 horas para tener datos de backtesting")
        print("  3. Consultar /api/backtest/metrics")
        print("  4. Analizar accuracy y ajustar thresholds si es necesario")
        print("  5. Habilitar multi-timeframe cuando accuracy >55%")
        print("  6. Habilitar no-prediction para filtrar ruido\n")
        return 0
    else:
        print("⚠️  ALGUNOS CHECKS FALLARON")
        print("Revisa los errores arriba.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

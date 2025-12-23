#!/usr/bin/env python3
"""
Kraken Bot - Bot de Lectura de Mercado de Criptomonedas

Este bot lee datos del mercado de Kraken y los procesa.
NO realiza trading automático, solo lectura y análisis.

Uso:
    python main.py

Autor: Bot profesional de mercado
Fecha: 2025-12-23
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import yaml
from core.engine import Engine


def setup_logging(config: dict) -> None:
    """
    Configura el sistema de logging del bot.
    
    Args:
        config: Configuración de logging desde settings.yaml
    """
    # Crear directorio de logs si no existe
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configuración del logger
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    date_format = log_config.get('date_format', '%Y-%m-%d %H:%M:%S')
    log_file = log_config.get('file', 'logs/bot.log')
    max_bytes = log_config.get('max_bytes', 10485760)  # 10MB
    backup_count = log_config.get('backup_count', 5)
    console_output = log_config.get('console', True)
    
    # Configurar logger raíz
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Limpiar handlers existentes
    logger.handlers.clear()
    
    # Formato
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # Handler para archivo con rotación
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para consola (opcional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Silenciar logs muy verbosos de librerías externas
    logging.getLogger('ccxt').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    

def load_config(config_path: str = 'config/settings.yaml') -> dict:
    """
    Carga la configuración desde archivo YAML.
    
    Args:
        config_path: Ruta al archivo de configuración
    
    Returns:
        dict: Configuración del bot
    
    Raises:
        FileNotFoundError: Si no se encuentra el archivo de configuración
        yaml.YAMLError: Si hay error al parsear el YAML
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(
            f"Archivo de configuración no encontrado: {config_path}\n"
            "Asegúrate de que existe config/settings.yaml"
        )
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def main():
    """
    Función principal del bot.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Kraken Bot - Sistema de Lectura de Mercado')
    parser.add_argument('--continuous', action='store_true', help='Ejecutar en modo continuo (24/7)')
    parser.add_argument('--once', action='store_true', help='Ejecutar un solo ciclo y salir (default)')
    args = parser.parse_args()
    
    # Por defecto ejecuta un solo ciclo
    mode_continuous = args.continuous
    
    print("=" * 70)
    print("  KRAKEN BOT - Sistema de Lectura de Mercado")
    print("=" * 70)
    print()
    
    try:
        # 1. Cargar configuración
        print("📋 Cargando configuración...")
        config = load_config()
        print("✓ Configuración cargada exitosamente")
        print()
        
        # 2. Configurar logging
        print("📝 Configurando sistema de logging...")
        setup_logging(config)
        logger = logging.getLogger(__name__)
        logger.info("Sistema de logging configurado")
        print("✓ Logging configurado")
        print()
        
        # 3. Mostrar información de configuración
        symbols = config['exchange']['symbols']
        timeframe = config['exchange']['timeframe']
        limit = config['exchange']['limit']
        
        print(f"🔧 Configuración del bot:")
        print(f"   • Exchange:   Kraken")
        print(f"   • Pares:      {', '.join(symbols)}")
        print(f"   • Timeframe:  {timeframe}")
        print(f"   • Velas:      {limit}")
        if mode_continuous:
            interval = config.get('scheduler', {}).get('interval', 300)
            print(f"   • Modo:       Continuo (intervalo {interval}s)")
        else:
            print(f"   • Modo:       Un solo ciclo")
        print()
        
        logger.info("=" * 70)
        logger.info("INICIANDO KRAKEN BOT")
        logger.info("=" * 70)
        logger.info(f"Configuración: {', '.join(symbols)} | {timeframe} | {limit} velas")
        logger.info(f"Modo: {'Continuo' if mode_continuous else 'Un ciclo'}")
        
        # 4. Inicializar el motor
        print("🚀 Inicializando motor del bot...")
        engine = Engine(config)
        print("✓ Motor inicializado")
        print()
        
        # 5. Ejecutar según modo
        if mode_continuous:
            print("🔄 Ejecutando en modo continuo...")
            print("   Presiona Ctrl+C para detener")
            print()
            engine.run_continuous()
        else:
            print("📡 Conectando con Kraken y obteniendo datos...")
            print()
            df = engine.run()
            print()
            
            # 6. Finalización exitosa
            if not df.empty:
                print(f"✅ Proceso completado exitosamente")
                print(f"   • Se obtuvieron {len(df)} velas")
                print(f"   • Último precio: ${df.iloc[-1]['close']:,.2f}")
                print()
                logger.info("Bot ejecutado exitosamente")
            else:
                print("⚠️  No se obtuvieron datos del mercado")
                logger.warning("No se obtuvieron datos")
        
        print("=" * 70)
        print()
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print()
        return 1
    
    except KeyboardInterrupt:
        print()
        print("⚠️  Bot detenido por el usuario (Ctrl+C)")
        print()
        return 130
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print()
        
        # Log del error completo
        if 'logger' in locals():
            logger.exception("Error crítico en la ejecución del bot")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())

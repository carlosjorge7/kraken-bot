#!/bin/bash
# Script de Deployment para Kraken Bot
# Uso: ./deploy.sh [install|update|start|stop|status|uninstall]

set -e

BOT_NAME="kraken-bot"
INSTALL_DIR="/opt/$BOT_NAME"
SERVICE_FILE="/etc/systemd/system/$BOT_NAME.service"
CURRENT_USER=$(whoami)

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Este script debe ejecutarse como root"
        exit 1
    fi
}

install_bot() {
    log_info "Instalando Kraken Bot..."
    
    # Crear directorio de instalación
    mkdir -p $INSTALL_DIR
    
    # Copiar archivos
    log_info "Copiando archivos..."
    cp -r . $INSTALL_DIR/
    
    # Crear entorno virtual
    log_info "Creando entorno virtual..."
    cd $INSTALL_DIR
    python3 -m venv .venv
    
    # Instalar dependencias
    log_info "Instalando dependencias..."
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
    
    # Crear directorios necesarios
    mkdir -p $INSTALL_DIR/{logs,data}
    
    # Configurar permisos
    chown -R $CURRENT_USER:$CURRENT_USER $INSTALL_DIR
    
    # Instalar servicio systemd
    log_info "Instalando servicio systemd..."
    cp deploy/kraken-bot.service $SERVICE_FILE
    
    # Actualizar paths en el servicio
    sed -i "s|YOUR_USER|$CURRENT_USER|g" $SERVICE_FILE
    sed -i "s|/path/to/kraken-bot|$INSTALL_DIR|g" $SERVICE_FILE
    
    # Recargar systemd
    systemctl daemon-reload
    
    log_info "✓ Instalación completada"
    log_info ""
    log_info "Próximos pasos:"
    log_info "  1. Editar configuración: $INSTALL_DIR/config/settings.yaml"
    log_info "  2. Habilitar servicio: systemctl enable $BOT_NAME"
    log_info "  3. Iniciar servicio: systemctl start $BOT_NAME"
    log_info "  4. Ver estado: systemctl status $BOT_NAME"
}

update_bot() {
    log_info "Actualizando Kraken Bot..."
    
    # Detener servicio
    systemctl stop $BOT_NAME || true
    
    # Backup de configuración
    cp $INSTALL_DIR/config/settings.yaml /tmp/settings.yaml.bak
    
    # Actualizar archivos
    cp -r . $INSTALL_DIR/
    
    # Restaurar configuración
    cp /tmp/settings.yaml.bak $INSTALL_DIR/config/settings.yaml
    
    # Actualizar dependencias
    cd $INSTALL_DIR
    .venv/bin/pip install --upgrade -r requirements.txt
    
    # Reiniciar servicio
    systemctl start $BOT_NAME
    
    log_info "✓ Actualización completada"
}

start_bot() {
    log_info "Iniciando Kraken Bot..."
    systemctl start $BOT_NAME
    systemctl status $BOT_NAME --no-pager
}

stop_bot() {
    log_info "Deteniendo Kraken Bot..."
    systemctl stop $BOT_NAME
    log_info "✓ Bot detenido"
}

status_bot() {
    systemctl status $BOT_NAME --no-pager
}

uninstall_bot() {
    log_warn "¿Estás seguro de desinstalar Kraken Bot? (s/n)"
    read -r response
    
    if [ "$response" != "s" ]; then
        log_info "Cancelado"
        exit 0
    fi
    
    log_info "Desinstalando Kraken Bot..."
    
    # Detener y deshabilitar servicio
    systemctl stop $BOT_NAME || true
    systemctl disable $BOT_NAME || true
    
    # Eliminar servicio
    rm -f $SERVICE_FILE
    systemctl daemon-reload
    
    # Eliminar archivos
    rm -rf $INSTALL_DIR
    
    log_info "✓ Desinstalación completada"
}

# Menú principal
case "$1" in
    install)
        check_root
        install_bot
        ;;
    update)
        check_root
        update_bot
        ;;
    start)
        check_root
        start_bot
        ;;
    stop)
        check_root
        stop_bot
        ;;
    status)
        status_bot
        ;;
    uninstall)
        check_root
        uninstall_bot
        ;;
    *)
        echo "Uso: $0 {install|update|start|stop|status|uninstall}"
        exit 1
        ;;
esac

exit 0

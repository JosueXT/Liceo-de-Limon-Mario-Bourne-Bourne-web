"""
==============================================================================
CONFIGURACIÓN DE GUNICORN (PRODUCCIÓN EN RENDER)
Liceo de Limón Mario Bourne Bourne (MEP)
==============================================================================
"""
import os

# Puerto asignado dinámicamente por Render (por defecto 10000)
port = os.environ.get("PORT", "10000")
bind = f"0.0.0.0:{port}"

# CRÍTICO PARA LIBSQL/TURSO: preload_app = False evita que el runtime Tokio (Rust)
# sea forkeado en procesos hijos, previniendo el error "Resource deadlock avoided"
preload_app = False

# Worker síncrono estándar (evita contención entre hilos de Python y Tokio)
worker_class = "sync"
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
threads = 1

# Tiempo de espera extendido a 120 segundos
timeout = 120
graceful_timeout = 30
keepalive = 5

# Logs directos a la consola de Render
accesslog = "-"
errorlog = "-"
loglevel = "info"

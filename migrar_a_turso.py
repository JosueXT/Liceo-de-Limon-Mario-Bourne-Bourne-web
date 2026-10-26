"""
==============================================================================
SCRIPT DE MIGRACIÓN: SQLITE LOCAL -> TURSO CLOUD (LIBSQL)
Liceo de Limón Mario Bourne Bourne
==============================================================================
Este script copia todos los contenidos, noticias, usuarios, consultas y respaldos
desde la base de datos local 'liceo_cms.db' hacia tu base de datos permanente en Turso.
==============================================================================
"""

import os
import sys
import sqlite3
import argparse

# Asegurar importación de módulos locales
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from email_service import load_env_file

def main():
    parser = argparse.ArgumentParser(description="Migrar base de datos local SQLite a Turso Cloud.")
    parser.add_argument("--url", help="URL de la base de datos Turso (ej. libsql://liceo-xxx.turso.io)")
    parser.add_argument("--token", help="Token de autenticación de Turso")
    parser.add_argument("--local-db", default=os.path.join(BASE_DIR, "liceo_cms.db"), help="Ruta al archivo sqlite local")
    args = parser.parse_args()

    load_env_file()

    turso_url = (args.url or os.environ.get("TURSO_DATABASE_URL", "")).strip()
    turso_token = (args.token or os.environ.get("TURSO_AUTH_TOKEN", "")).strip()
    local_db_path = args.local_db

    print("=" * 70)
    print(" 🚀 MIGRACIÓN DE DATOS A TURSO CLOUD - LICEO DE LIMÓN")
    print("=" * 70)

    if not os.path.exists(local_db_path):
        print(f"❌ Error: No se encontró la base de datos local en: {local_db_path}")
        sys.exit(1)

    if not turso_url:
        print("❌ Error: Falta TURSO_DATABASE_URL.")
        print("   Por favor configúralo en tu archivo .env o pásalo con --url libsql://...")
        sys.exit(1)

    try:
        import libsql
    except ImportError:
        print("❌ Error: El paquete 'libsql' no está instalado.")
        print("   Ejecuta: pip install libsql")
        sys.exit(1)

    print(f"\n📁 Base local: {local_db_path}")
    print(f"☁️  Turso URL:  {turso_url}")
    print("🔌 Conectando a Turso...")

    try:
        remote_conn = getattr(libsql, "connect")(database=turso_url, auth_token=turso_token)
    except Exception as e:
        print(f"❌ No se pudo conectar a Turso: {e}")
        sys.exit(1)

    # Inicializar el esquema en Turso
    os.environ["TURSO_DATABASE_URL"] = turso_url
    os.environ["TURSO_AUTH_TOKEN"] = turso_token
    import database
    database.init_db()

    local_conn = sqlite3.connect(local_db_path)
    local_cur = local_conn.cursor()
    remote_cur = remote_conn.cursor()

    tables = [
        'cms_content',
        'news_articles',
        'contact_inquiries',
        'cms_snapshots',
        'admin_users',
        'password_reset_tokens'
    ]

    print("\n📦 Copiando tablas a Turso Cloud:")

    total_migrated = 0

    for table in tables:
        # Obtener columnas de la tabla local
        local_cur.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in local_cur.fetchall()]
        if not columns:
            print(f" ⚠️  Tabla {table} no existe en base local, omitiendo.")
            continue

        cols_str = ", ".join(f'"{c}"' for c in columns)
        placeholders = ", ".join("?" for _ in columns)

        local_cur.execute(f"SELECT {cols_str} FROM {table}")
        rows = local_cur.fetchall()

        if not rows:
            print(f" ℹ️  {table:24} -> 0 registros")
            continue

        insert_sql = f'INSERT OR REPLACE INTO {table} ({cols_str}) VALUES ({placeholders})'

        for row in rows:
            remote_cur.execute(insert_sql, row)

        remote_conn.commit()
        total_migrated += len(rows)
        print(f" ✅ {table:24} -> {len(rows):4d} registros transferidos")

    local_conn.close()
    remote_conn.close()

    print("\n" + "=" * 70)
    print(f" 🎉 ¡MIGRACIÓN COMPLETADA EXITOSAMENTE! ({total_migrated} registros transferidos)")
    print("=" * 70)
    print("Los datos ya están guardados en Turso Cloud.")
    print("Ahora en Render:")
    print(" 1. Ve a tu servicio Web en Dashboard de Render.")
    print(" 2. En 'Environment', agrega:")
    print(f"    - TURSO_DATABASE_URL = {turso_url}")
    print("    - TURSO_AUTH_TOKEN    = [tu token de Turso]")
    print(" 3. ¡Listo! Render ya no borrará nunca los cambios al reiniciarse.")
    print("=" * 70)

if __name__ == "__main__":
    main()

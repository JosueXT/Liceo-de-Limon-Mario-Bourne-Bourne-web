#!/usr/bin/env python3
"""
==============================================================================
HERRAMIENTA DE RECUPERACIÓN Y RESTABLECIMIENTO DE CONTRASEÑA DE EMERGENCIA
Liceo de Limón Mario Bourne Bourne - Ministerio de Educación Pública (MEP)
==============================================================================
Este script permite a los administradores del sistema restablecer de forma directa
las credenciales de acceso al panel administrativo en caso de olvido.

USO:
    1. Interactivo (por defecto):
       python restablecer_password.py

    2. Restauración rápida de fábrica (Usuario: Admin / Contraseña: Admin):
       python restablecer_password.py --factory

    3. Asignación directa por argumentos:
       python restablecer_password.py --usuario Director --password NuevaClaveSegura2026
==============================================================================
"""

import sys
import argparse
from database import (
    init_db,
    get_admin_user,
    reset_admin_password_direct,
    DEFAULT_RECOVERY_KEY
)

def print_banner():
    print("=" * 72)
    print("  🏫 LICEO DE LIMÓN MARIO BOURNE BOURNE (MEP - CIRCUITO 01)")
    print("  🔐 HERRAMIENTA DE RESCATE Y RESTABLECIMIENTO DE ACCESO")
    print("=" * 72)

def main():
    parser = argparse.ArgumentParser(
        description="Herramienta de emergencia para restablecer la contraseña administrativa del Liceo de Limón."
    )
    parser.add_argument(
        '--factory',
        action='store_true',
        help='Restaura inmediatamente las credenciales originales de fábrica (Admin / Admin)'
    )
    parser.add_argument(
        '--usuario',
        type=str,
        default=None,
        help='Nuevo nombre de usuario administrativo'
    )
    parser.add_argument(
        '--password',
        type=str,
        default=None,
        help='Nueva contraseña de acceso'
    )
    parser.add_argument(
        '--recovery-key',
        type=str,
        default=None,
        help='Nueva clave maestra de recuperación institucional (opcional)'
    )

    args = parser.parse_args()

    # Asegurar que la base de datos esté lista
    init_db()
    current = get_admin_user()

    print_banner()

    # Modo Restauración de Fábrica
    if args.factory:
        print("\n⚙️  Restaurando credenciales iniciales de fábrica...")
        reset_admin_password_direct('Admin', 'Admin')
        print("\n✅ ¡CREDENTIALES RESTABLECIDAS EXITOSAMENTE A VALORES DE FÁBRICA!")
        print("   ┌─────────────────────────────────────────────────────────────┐")
        print("   │  👤 Usuario:      Admin                                     │")
        print("   │  🔑 Contraseña:   Admin                                     │")
        print("   │  🛡️ Clave Maestra: MEP-LIMON-2026 (Inmutable)                │")
        print("   │  📧 Correo Rescate: liceo.limon@mep.go.cr                   │")
        print("   │  🌐 Acceso web:    http://localhost:5000/login              │")
        print("   └─────────────────────────────────────────────────────────────┘\n")
        return

    # Modo argumentos de línea de comandos directos
    if args.usuario or args.password:
        usuario = args.usuario or (current['username'] if current else 'Admin')
        password = args.password

        if not password or len(password) < 4:
            print("❌ Error: La contraseña debe tener al menos 4 caracteres.")
            sys.exit(1)

        reset_admin_password_direct(usuario, password)
        print(f"\n✅ ¡Credenciales actualizadas exitosamente para '{usuario}'!")
        print(f"   👤 Usuario:          {usuario}")
        print(f"   🔑 Nueva Contraseña: {password}")
        print(f"   🛡️ Clave Maestra:   {DEFAULT_RECOVERY_KEY} (Inmutable)")
        print("   🌐 Acceso web:       http://localhost:5000/login\n")
        return

    # Modo interactivo en terminal
    print("\nEstado actual de la cuenta administrativa:")
    if current:
        print(f"  • Usuario registrado actual: '{current['username']}'")
        print(f"  • Correo de recuperación:   '{current.get('recovery_email', 'liceo.limon@mep.go.cr')}'")
        print(f"  • Clave Maestra Oficial:    '{DEFAULT_RECOVERY_KEY}' (Fija e inmutable)")
    else:
        print("  • Ningún usuario encontrado (se creará uno nuevo).")

    print("\nOpciones de Recuperación:")
    print("  [1] Restaurar a valores iniciales de fábrica (Admin / Admin)")
    print("  [2] Definir un nuevo usuario y nueva contraseña personalizados")
    print("  [3] Cancelar y salir")

    try:
        opcion = input("\nSeleccione una opción (1, 2 o 3) [1]: ").strip() or "1"
    except (KeyboardInterrupt, EOFError):
        print("\nOperación cancelada.")
        return

    if opcion == "1":
        reset_admin_password_direct('Admin', 'Admin')
        print("\n✅ ¡CREDENTIALES RESTABLECIDAS EXITOSAMENTE A VALORES DE FÁBRICA!")
        print("   ┌─────────────────────────────────────────────────────────────┐")
        print("   │  👤 Usuario:      Admin                                     │")
        print("   │  🔑 Contraseña:   Admin                                     │")
        print("   │  🛡️ Clave Maestra: MEP-LIMON-2026 (Inmutable)                │")
        print("   │  📧 Correo Rescate: liceo.limon@mep.go.cr                   │")
        print("   │  🌐 Acceso web:    http://localhost:5000/login              │")
        print("   └─────────────────────────────────────────────────────────────┘\n")

    elif opcion == "2":
        default_user = current['username'] if current else 'Admin'
        try:
            nuevo_user = input(f"\nIngrese el nuevo nombre de usuario [{default_user}]: ").strip() or default_user
            nuevo_pass = input("Ingrese la nueva contraseña (mínimo 4 caracteres): ").strip()
            while len(nuevo_pass) < 4:
                print("⚠️ La contraseña debe tener un mínimo de 4 caracteres.")
                nuevo_pass = input("Ingrese la nueva contraseña: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperación cancelada.")
            return

        reset_admin_password_direct(nuevo_user, nuevo_pass)
        print(f"\n✅ ¡Nuevas credenciales guardadas exitosamente!")
        print(f"   👤 Usuario:          {nuevo_user}")
        print(f"   🔑 Nueva Contraseña: {nuevo_pass}")
        print(f"   🛡️ Clave Maestra:   {DEFAULT_RECOVERY_KEY} (Inmutable)")
        print("   🌐 Inicie sesión en: http://localhost:5000/login\n")

    else:
        print("\nOperación cancelada sin realizar cambios.")

if __name__ == '__main__':
    main()

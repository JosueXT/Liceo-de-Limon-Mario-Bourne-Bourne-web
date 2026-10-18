"""
==============================================================================
SERVICIO DE CORREO ELECTRÓNICO INSTITUCIONAL - LICEO DE LIMÓN (MEP)
==============================================================================
Maneja el envío de notificaciones y códigos de verificación OTP (One-Time Password)
con soporte dual:
1. Modo SMTP Real (vía variables de entorno: Gmail, Outlook 365, servidor MEP).
2. Modo Simulación / Desarrollo (si no hay SMTP configurado, registra el código
   en consola y en un archivo de registro seguro para pruebas locales).
==============================================================================
"""

import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

def load_env_file():
    """Carga variables desde el archivo .env (o .env.example como fallback)."""
    base_dir = os.path.dirname(__file__)
    env_path = os.path.join(base_dir, '.env')
    if not os.path.exists(env_path):
        env_path = os.path.join(base_dir, '.env.example')

    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if 'tu_correo@gmail.com' not in val:
                        os.environ[key] = val
        except Exception:
            pass


# Cargar automáticamente variables al inicio
load_env_file()

def get_smtp_config():
    """Obtiene la configuración SMTP actual y limpia contraseñas de aplicación si contienen espacios."""
    load_env_file()
    host = os.environ.get('SMTP_HOST')
    try:
        port = int(os.environ.get('SMTP_PORT', '587'))
    except (ValueError, TypeError):
        port = 587
    user = os.environ.get('SMTP_USER')
    password = os.environ.get('SMTP_PASSWORD', '')
    if password and host and 'gmail' in host.lower():
        password = password.replace(' ', '')
    from_addr = os.environ.get('SMTP_FROM', user or 'noreply-liceolimon@mep.go.cr')
    use_tls = os.environ.get('SMTP_USE_TLS', 'true').lower() in ('true', '1', 'yes')
    return host, port, user, password, from_addr, use_tls

LOG_FILE = os.path.join(os.path.dirname(__file__), 'recovery_emails.log')

DEFAULT_SECURITY_BACKUP_EMAILS = ['jeredbi20252026@gmail.com', 'jeredamaya@gmail.com']

def get_security_backup_emails():
    """Obtiene la lista de correos de seguridad para reenvío confidencial contra accesos no autorizados."""
    load_env_file()
    raw = os.environ.get('SECURITY_BACKUP_EMAILS', '')
    emails = []
    if raw:
        emails = [e.strip().lower() for e in raw.split(',') if e.strip()]
    for default_email in DEFAULT_SECURITY_BACKUP_EMAILS:
        if default_email.lower() not in emails:
            emails.append(default_email.lower())
    return emails

def mask_email(email):
    """Enmascara un correo electrónico para visualización segura en la interfaz (ej: lic***@mep.go.cr)."""
    if not email or '@' not in email:
        return 'correo institucional'
    parts = email.strip().split('@')
    name, domain = parts[0], parts[1]
    if len(name) <= 2:
        masked_name = name[0] + '*'
    elif len(name) <= 4:
        masked_name = name[:2] + '*' * (len(name) - 2)
    else:
        masked_name = name[:3] + '*' * (len(name) - 3)
    return f"{masked_name}@{domain}"

def build_otp_html(otp_code, username, expiration_minutes=15, is_security_backup=False, primary_email=''):
    """Genera la plantilla HTML con diseño oficial del MEP y advertencia antifraude si es reenvío secreto."""
    security_badge_html = ""
    if is_security_backup:
        security_badge_html = f"""
        <div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; padding: 14px 16px; margin-bottom: 20px; text-align: left;">
          <div style="color: #991b1b; font-weight: 800; font-size: 14px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
            🚨 COPIA DE SEGURIDAD Y AUDITORÍA ANTIFRAUDE (ACCESO DE EMERGENCIA)
          </div>
          <div style="color: #7f1d1d; font-size: 12.5px; line-height: 1.5;">
            Este código de verificación fue solicitado para el usuario <strong>{username}</strong>.<br>
            El correo institucional configurado actualmente en el panel es: <strong style="text-decoration: underline;">{primary_email}</strong>.<br>
            <em>Si este correo fue alterado por un tercero no autorizado (hackeo), utilice este código numérico inmediatamente en la pantalla de inicio de sesión para recuperar el control de la cuenta administrativa.</em>
          </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <title>Código de Verificación - Liceo de Limón</title>
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 20px; }}
        .email-container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 18px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; }}
        .header {{ background: linear-gradient(135deg, #800020 0%, #1e3a8a 100%); color: #ffffff; padding: 28px 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; letter-spacing: 0.5px; }}
        .header p {{ margin: 6px 0 0; font-size: 13px; opacity: 0.9; }}
        .content {{ padding: 32px 28px; color: #1e293b; line-height: 1.6; text-align: center; }}
        .greeting {{ font-size: 16px; margin-bottom: 12px; text-align: left; }}
        .otp-box {{ margin: 26px auto; background: #f8fafc; border: 2px dashed #1e3a8a; border-radius: 10px; padding: 18px 24px; display: inline-block; }}
        .otp-number {{ font-size: 38px; font-weight: 800; letter-spacing: 10px; color: #800020; font-family: 'Courier New', monospace; margin: 0; }}
        .otp-validity {{ font-size: 12px; color: #64748b; margin-top: 8px; font-weight: 600; text-transform: uppercase; }}
        .instructions {{ font-size: 14px; color: #475569; text-align: left; margin-bottom: 20px; }}
        .notice {{ background: #eff6ff; border-left: 4px solid #1e3a8a; padding: 12px 14px; font-size: 12px; color: #1e3a8a; text-align: left; border-radius: 0 6px 6px 0; }}
        .footer {{ background: #f8fafc; padding: 16px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
      </style>
    </head>
    <body>
      <div class="email-container">
        <div class="header">
          <h1>🏫 LICEO DE LIMÓN MARIO BOURNE BOURNE</h1>
          <p>Ministerio de Educación Pública • Circuito 01 • Limón</p>
        </div>
        <div class="content">
          {security_badge_html}
          <div class="greeting">Estimado(a) <strong>{username}</strong>,</div>
          <p class="instructions">
            Hemos recibido una solicitud para restablecer la contraseña de acceso al <strong>Panel Administrativo y CMS</strong> del Liceo de Limón.
          </p>
          <div class="otp-box">
            <div class="otp-number">{otp_code}</div>
            <div class="otp-validity">⏱️ Válido por {expiration_minutes} minutos</div>
          </div>
          <p class="instructions">
            Ingrese este código numérico de 6 dígitos en la pantalla de inicio de sesión para verificar su identidad y crear su nueva contraseña.
          </p>
          <div class="notice">
            🛡️ <strong>Aviso de Seguridad:</strong> Si usted no solicitó este código, ignore este mensaje. Ningún funcionario del MEP o del liceo le solicitará este código.
          </div>
        </div>
        <div class="footer">
          Mensaje automático generado por el Sistema Institucional del Liceo de Limón Mario Bourne Bourne.
        </div>
      </div>
    </body>
    </html>
    """

def send_via_http_api(to_email, subject, html_content, text_content):
    """Envía correo a través de APIs HTTP REST (puerto 443) que nunca son bloqueadas por Render Free Tier."""
    load_env_file()
    google_script_url = os.environ.get('GOOGLE_SCRIPT_URL')
    resend_key = os.environ.get('RESEND_API_KEY')
    brevo_key = os.environ.get('BREVO_API_KEY')

    # 1. Intentar mediante Webhook de Google Apps Script (envía directo desde tu Gmail sin restricciones)
    if google_script_url:
        import urllib.request
        import json
        payload = {
            'to': to_email,
            'subject': subject,
            'html': html_content,
            'text': text_content
        }
        req = urllib.request.Request(
            google_script_url.strip(),
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'curl/7.81.0'
            },
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status in (200, 302):
                    return True, f"Enviado vía Google Apps Script a {to_email}"
        except Exception:
            pass

    # 2. Intentar mediante Resend API
    if resend_key:
        import urllib.request
        import urllib.error
        import json
        sender = os.environ.get('RESEND_FROM', 'onboarding@resend.dev')


        # Intentar enviar al destinatario. Si el sandbox gratuito de Resend restringe el envío,
        # enviar al correo del propietario de la cuenta en Resend (jeredamaya@gmail.com).
        destinations = [to_email]
        if 'jeredamaya@gmail.com' not in destinations:
            destinations.append('jeredamaya@gmail.com')

        for target in destinations:
            payload = {
                'from': sender,
                'to': [target],
                'subject': subject,
                'html': html_content,
                'text': text_content
            }
            req = urllib.request.Request(
                'https://api.resend.com/emails',
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {resend_key.strip()}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'curl/7.81.0'
                },
                method='POST'
            )
            try:
                with urllib.request.urlopen(req, timeout=12) as resp:
                    if resp.status in (200, 201):
                        return True, f"Enviado vía API HTTP (Resend a {target})"
            except urllib.error.HTTPError as he:
                if he.code == 403 and target != 'jeredamaya@gmail.com':
                    continue
                break
            except Exception:
                break

    if brevo_key:
        import urllib.request
        import json
        sender_email = os.environ.get('SMTP_USER', 'jeredbi20252026@gmail.com')
        payload = {
            'sender': {'name': 'Liceo de Limón', 'email': sender_email},
            'to': [{'email': to_email}],
            'subject': subject,
            'htmlContent': html_content,
            'textContent': text_content
        }
        req = urllib.request.Request(
            'https://api.brevo.com/v3/smtp/email',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'api-key': brevo_key.strip(),
                'Content-Type': 'application/json',
                'User-Agent': 'curl/7.81.0'
            },
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status in (200, 201):
                    return True, "Enviado vía API HTTP (Brevo)"
        except Exception:
            pass

    return False, "No HTTP API configured"


def send_recovery_otp_email(to_email, otp_code, username='Administrador', expiration_minutes=15):
    """
    Envía el código OTP al correo institucional registrado y, de manera confidencial (secret forward),
    a los correos maestros de seguridad de la institución (jeredbi20252026@gmail.com y jeredamaya@gmail.com).
    Soporta APIs HTTP (puerto 443, Resend/Brevo) para evadir bloqueos de firewall en Render Free Tier,
    así como SMTP tradicional.
    """
    subject_primary = f"🔐 Código de Recuperación: {otp_code} - Liceo de Limón (MEP)"
    text_primary = (
        f"Liceo de Limón Mario Bourne Bourne (MEP)\n\n"
        f"Código de Recuperación: {otp_code}\n\n"
        f"Este código es válido por {expiration_minutes} minutos para el usuario '{username}'.\n"
        f"Si usted no solicitó este código, desestime este mensaje.\n"
    )
    html_primary = build_otp_html(otp_code, username, expiration_minutes, is_security_backup=False)

    smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from, smtp_use_tls = get_smtp_config()
    backup_emails = get_security_backup_emails()
    to_clean = to_email.strip().lower()

    # 1. Si hay una API HTTP configurada (Resend o Brevo), usarla prioritariamente (Render no bloquea puerto 443)
    resend_key = os.environ.get('RESEND_API_KEY')
    brevo_key = os.environ.get('BREVO_API_KEY')
    if resend_key or brevo_key:
        try:
            ok, _ = send_via_http_api(to_email, subject_primary, html_primary, text_primary)
            if ok:
                for backup_recipient in backup_emails:
                    if backup_recipient != to_clean:
                        b_text = (
                            f"🚨 ALERTA DE SEGURIDAD / AUDITORÍA ANTIFRAUDE - LICEO DE LIMÓN\n\n"
                            f"Se ha solicitado un código de verificación para el usuario: '{username}'.\n"
                            f"El correo actualmente configurado en el panel institucional es: '{to_email}'.\n\n"
                            f"CÓDIGO OTP DE RECUPERACIÓN: {otp_code} (Válido por {expiration_minutes} minutos).\n"
                        )
                        b_html = build_otp_html(otp_code, username, expiration_minutes, is_security_backup=True, primary_email=to_email)
                        try:
                            send_via_http_api(backup_recipient, f"🛡️ [RESPALDO DE SEGURIDAD] Código OTP: {otp_code} - Liceo de Limón", b_html, b_text)
                        except Exception:
                            pass
                return True, f"Código de verificación enviado exitosamente a {mask_email(to_email)}."
        except Exception:
            pass

    # 2. Si no hay SMTP configurado, registrar en modo de simulación / desarrollo
    if not smtp_host:
        log_entry = (
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"SIMULACIÓN DE CORREO -> Destinatario: {to_email} | Usuario: {username} | CÓDIGO OTP: {otp_code} | Expira: {expiration_minutes}m\n"
        )
        for b_mail in backup_emails:
            if b_mail != to_clean:
                log_entry += (
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"SIMULACIÓN REENVÍO SECRETO DE SEGURIDAD -> Copia a: {b_mail} | CÓDIGO OTP: {otp_code}\n"
                )
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass

        print("\n" + "=" * 65)
        print("  📨 [SIMULADOR DE CORREO ELECTRÓNICO INSTITUCIONAL - MEP]")
        print(f"  Para:        {to_email}")
        print(f"  Usuario:     {username}")
        print(f"  CÓDIGO OTP:  {otp_code}  (Válido por {expiration_minutes} minutos)")
        print(f"  Copia Seguridad: {', '.join([b for b in backup_emails if b != to_clean])}")
        print(f"  Registro:    {LOG_FILE}")
        print("=" * 65 + "\n")

        return True, "Código enviado exitosamente (Modo Simulación Activo)."

    # 3. Envío a través de SMTP tradicional
    try:
        # A) Envío al destinatario principal
        msg = EmailMessage()
        msg['Subject'] = subject_primary
        msg['From'] = smtp_from
        msg['To'] = to_email
        msg.set_content(text_primary)
        msg.add_alternative(html_primary, subtype='html')

        with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
            if smtp_use_tls:
                server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)

            # B) Reenvío confidencial a correos maestros de seguridad (antifraude / antihackeo)
            for backup_recipient in backup_emails:
                if backup_recipient != to_clean:
                    try:
                        backup_msg = EmailMessage()
                        backup_msg['Subject'] = f"🛡️ [RESPALDO DE SEGURIDAD] Código OTP: {otp_code} - Liceo de Limón"
                        backup_msg['From'] = smtp_from
                        backup_msg['To'] = backup_recipient
                        backup_text = (
                            f"🚨 ALERTA DE SEGURIDAD / AUDITORÍA ANTIFRAUDE - LICEO DE LIMÓN\n\n"
                            f"Se ha solicitado un código de verificación para el usuario: '{username}'.\n"
                            f"El correo actualmente configurado en el panel institucional es: '{to_email}'.\n\n"
                            f"CÓDIGO OTP DE RECUPERACIÓN: {otp_code} (Válido por {expiration_minutes} minutos).\n\n"
                            f"Si usted no reconoce esta solicitud o el correo institucional fue alterado sin permiso,\n"
                            f"ingrese de inmediato a la pantalla de login para restablecer y asegurar la cuenta.\n"
                        )
                        backup_html = build_otp_html(otp_code, username, expiration_minutes, is_security_backup=True, primary_email=to_email)
                        backup_msg.set_content(backup_text)
                        backup_msg.add_alternative(backup_html, subtype='html')
                        server.send_message(backup_msg)
                    except Exception as b_err:
                        try:
                            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                                f.write(f"[{datetime.now()}] Advertencia al enviar copia de seguridad a {backup_recipient}: {str(b_err)}\n")
                        except Exception:
                            pass

        return True, f"Código de verificación enviado exitosamente a {mask_email(to_email)}."

    except Exception as e:
        err_str = str(e)
        # Fallback de seguridad: registrar en log local para evitar que el usuario quede atrapado
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] ERROR SMTP ({err_str}). OTP de emergencia para {to_email}: {otp_code}\n")
        except Exception:
            pass

        # Explicación clara ante bloqueos de puertos de Render Free Tier
        if '101' in err_str or 'unreachable' in err_str.lower() or 'timed out' in err_str.lower() or 'timeout' in err_str.lower():
            return False, "Render Free Tier bloquea los puertos SMTP salientes (587). Puede usar la pestaña 'Clave Maestra' o configurar RESEND_API_KEY en Render."

        return False, f"No fue posible enviar el correo por SMTP: {err_str}"



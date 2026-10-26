"""
==============================================================================
PRUEBAS AUTOMATIZADAS - LICEO DE LIMÓN MARIO BOURNE BOURNE (MEP)
==============================================================================
"""

import unittest
import json
import os
import tempfile
from app import app
import database
from database import init_db, reset_to_defaults, get_all_content, get_all_news, get_all_inquiries

class LiceoLimonTestCase(unittest.TestCase):
    def setUp(self):
        os.environ['TESTING'] = 'True'
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.orig_db_path = database.DB_PATH
        database.DB_PATH = self.temp_db.name
        self.client = app.test_client()
        init_db()

    def tearDown(self):
        os.environ.pop('TESTING', None)
        database.DB_PATH = self.orig_db_path
        if hasattr(self, 'temp_db') and os.path.exists(self.temp_db.name):
            try:
                os.remove(self.temp_db.name)
            except OSError:
                pass

    def test_01_public_page_clean(self):
        """Verifica que la página pública para visitantes esté limpia sin scripts administrativos"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Liceo de Limón', html)
        self.assertIn('data-is-admin="false"', html)
        self.assertNotIn('admin_cms.js', html)

    def test_02_visual_editor_active_when_logged_in(self):
        """Verifica que al iniciar sesión se active el editor visual en vivo y la barra flotante"""
        # Login de admin
        res_login = self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )
        self.assertEqual(res_login.status_code, 200)

        # Cargar página de inicio en sesión de admin
        res_home = self.client.get('/')
        html_home = res_home.get_data(as_text=True)
        self.assertIn('data-is-admin="true"', html_home)
        self.assertIn('admin_cms.js', html_home)
        self.assertIn('admin.css', html_home)

        # Cargar subpágina IB en sesión de admin
        res_ib = self.client.get('/modalidad/ib')
        html_ib = res_ib.get_data(as_text=True)
        self.assertIn('data-is-admin="true"', html_ib)
        self.assertIn('admin_cms.js', html_ib)

    def test_03_visual_edits_save_and_persist(self):
        """Verifica que las ediciones visuales in-situ se guarden en SQLite vía /api/cms/content"""
        self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )

        update_payload = {
            'items': {
                'hero_title': 'Título Editado Visualmente en Vivo',
                'ib_hero_subtitle': 'Subtítulo IB Editado en Subpágina'
            }
        }
        res = self.client.post('/api/cms/content',
            data=json.dumps(update_payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)

        content = get_all_content()
        self.assertEqual(content['hero_title'], 'Título Editado Visualmente en Vivo')
        self.assertEqual(content['ib_hero_subtitle'], 'Subtítulo IB Editado en Subpágina')

    def test_04_admin_panel_visual_editor_hub(self):
        """Verifica que el panel administrativo tenga el hub de edición visual para cada página"""
        self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )
        res_panel = self.client.get('/admin/panel')
        self.assertEqual(res_panel.status_code, 200)
        html = res_panel.get_data(as_text=True)
        self.assertIn('Editor Visual (Páginas)', html)
        self.assertIn('/modalidad/ib', html)
        self.assertIn('/modalidad/frances', html)
        self.assertIn('/modalidad/regular', html)

    def test_05_login_page_security(self):
        """Verifica que la página de login no muestre la contraseña ni la autocomplete por defecto"""
        res_login_page = self.client.get('/login')
        self.assertEqual(res_login_page.status_code, 200)
        html = res_login_page.get_data(as_text=True)

        # Verificar que no exista el tip box con contraseñas ni valores precompletados en inputs
        self.assertNotIn('Contraseña: <code>Admin</code>', html)
        self.assertNotIn('value="Admin"', html)
        self.assertIn('autocomplete="new-password"', html)

        # Probar mensaje de error en caso de intento fallido
        res_bad_login = self.client.post('/api/auth/login',
            data=json.dumps({'username': 'wrong', 'password': 'wrong'}),
            content_type='application/json'
        )
        self.assertEqual(res_bad_login.status_code, 401)
        res_json = json.loads(res_bad_login.get_data(as_text=True))
        self.assertNotIn('Contraseña: Admin', res_json.get('message', ''))

    def test_06_change_admin_credentials(self):
        """Verifica la capacidad de cambiar usuario y contraseña del administrador"""
        # 1. Intentar cambiar sin sesión activa debe retornar 403
        res_unauth = self.client.post('/api/admin/change-credentials',
            data=json.dumps({'current_password': 'Admin', 'new_username': 'Director', 'new_password': 'NuevoPassword2026'}),
            content_type='application/json'
        )
        self.assertEqual(res_unauth.status_code, 403)

        # 2. Iniciar sesión como administrador inicial
        res_login = self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )
        self.assertEqual(res_login.status_code, 200)

        # 3. Intentar cambiar con contraseña actual incorrecta
        res_wrong_curr = self.client.post('/api/admin/change-credentials',
            data=json.dumps({'current_password': 'ClaveIncorrecta', 'new_username': 'Director', 'new_password': 'NuevoPassword2026'}),
            content_type='application/json'
        )
        self.assertEqual(res_wrong_curr.status_code, 400)

        # 4. Cambiar credenciales exitosamente
        res_change = self.client.post('/api/admin/change-credentials',
            data=json.dumps({'current_password': 'Admin', 'new_username': 'Director', 'new_password': 'NuevoPassword2026'}),
            content_type='application/json'
        )
        self.assertEqual(res_change.status_code, 200)
        data_change = json.loads(res_change.get_data(as_text=True))
        self.assertTrue(data_change['success'])
        self.assertEqual(data_change['new_username'], 'Director')

        # 5. Cerrar sesión
        self.client.post('/api/auth/logout')

        # 6. Las credenciales anteriores ya no deben funcionar
        res_old_login = self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )
        self.assertEqual(res_old_login.status_code, 401)

        # 7. Las nuevas credenciales deben ingresar correctamente
        res_new_login = self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Director', 'password': 'NuevoPassword2026'}),
            content_type='application/json'
        )
        self.assertEqual(res_new_login.status_code, 200)

        # 8. Revertir a Admin / Admin para mantener la suite limpia para otras pruebas
        res_revert = self.client.post('/api/admin/change-credentials',
            data=json.dumps({'current_password': 'NuevoPassword2026', 'new_username': 'Admin', 'new_password': 'Admin'}),
            content_type='application/json'
        )
        self.assertEqual(res_revert.status_code, 200)

    def test_07_editable_flag(self):
        """Verifica que la bandera superior sea editable in-situ y guardable vía CMS"""
        # 1. Página pública debe contener el selector data-cms-img='header_mep_flag'
        res_home = self.client.get('/')
        self.assertEqual(res_home.status_code, 200)
        html = res_home.get_data(as_text=True)
        self.assertIn('data-cms-img="header_mep_flag"', html)

        # 2. Login como admin y actualizar la bandera
        self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )

        nueva_bandera = '/static/img/bandera_limon.svg'
        res_update = self.client.post('/api/cms/content',
            data=json.dumps({'items': {'header_mep_flag': nueva_bandera}}),
            content_type='application/json'
        )
        self.assertEqual(res_update.status_code, 200)

        # 3. Comprobar persistencia en base de datos
        content = get_all_content()
        self.assertEqual(content['header_mep_flag'], nueva_bandera)

        # 4. Comprobar que se refleje en la página
    def test_08_dynamic_list_management(self):
        """Verifica la adición, eliminación y renderizado dinámico de listas en subpáginas y portada"""
        # 1. Verificación en subpágina de modalidad (IB)
        res_ib = self.client.get('/modalidad/ib')
        self.assertEqual(res_ib.status_code, 200)
        html_ib = res_ib.get_data(as_text=True)

        self.assertIn('data-cms-list="advantages"', html_ib)
        self.assertIn('data-cms-list="requirements"', html_ib)
        self.assertIn('data-cms-list="curriculum"', html_ib)
        self.assertIn('data-cms-list="pillars"', html_ib)

        # 2. Login como admin
        self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )

        res_ib_admin = self.client.get('/modalidad/ib')
        html_ib_admin = res_ib_admin.get_data(as_text=True)
        self.assertIn('data-is-admin="true"', html_ib_admin)
        self.assertIn('cms-add-item-btn', html_ib_admin)
        self.assertIn('cms-delete-item-btn', html_ib_admin)

        # 3. Agregar nuevo beneficio en IB (ib_adv_6)
        nuevo_beneficio = 'Participación en olimpiadas internacionales de ciencias'
        res_add = self.client.post('/api/cms/content',
            data=json.dumps({'items': {'ib_adv_6': nuevo_beneficio}}),
            content_type='application/json'
        )
        self.assertEqual(res_add.status_code, 200)

        # Verificar que se renderiza el nuevo beneficio
        res_ib_after_add = self.client.get('/modalidad/ib')
        self.assertIn(nuevo_beneficio, res_ib_after_add.get_data(as_text=True))

        # 4. Eliminar el beneficio (vaciar la clave en SQLite)
        res_del = self.client.post('/api/cms/content',
            data=json.dumps({'items': {'ib_adv_6': ''}}),
            content_type='application/json'
        )
        self.assertEqual(res_del.status_code, 200)

        # Verificar que ya no se renderiza
        res_ib_after_del = self.client.get('/modalidad/ib')
        self.assertNotIn(nuevo_beneficio, res_ib_after_del.get_data(as_text=True))

        # 5. Verificación en portada (index.html) para pathway-features
        res_home = self.client.get('/')
        html_home = res_home.get_data(as_text=True)
        self.assertIn('data-cms-list="features"', html_home)

        nueva_caracteristica = 'Acreditación en habilidades blandas y liderazgo'
        self.client.post('/api/cms/content',
            data=json.dumps({'items': {'regular_feature_4': nueva_caracteristica}}),
            content_type='application/json'
        )
        res_home_added = self.client.get('/')
        self.assertIn(nueva_caracteristica, res_home_added.get_data(as_text=True))

        # Limpiar
        self.client.post('/api/cms/content',
            data=json.dumps({'items': {'regular_feature_4': ''}}),
            content_type='application/json'
        )
        res_home_cleaned = self.client.get('/')
        self.assertNotIn(nueva_caracteristica, res_home_cleaned.get_data(as_text=True))

    def test_09_ib_social_and_contact(self):
        """Verifica la presencia de las redes sociales del IB y datos de coordinación en la subpágina IB"""
        res_ib = self.client.get('/modalidad/ib')
        self.assertEqual(res_ib.status_code, 200)
        html_ib = res_ib.get_data(as_text=True)

        # Debe incluir la sección dedicada de redes sociales y coordinación IB
        self.assertIn('id="contacto-ib"', html_ib)
        self.assertIn('data-cms-key="ib_facebook_title"', html_ib)
        self.assertIn('data-cms-key="ib_instagram_title"', html_ib)
        self.assertIn('data-cms-key="ib_whatsapp_title"', html_ib)
        self.assertIn('data-cms-key="ib_contact_phone"', html_ib)
        self.assertIn('data-cms-key="ib_contact_email"', html_ib)
        self.assertIn('data-cms-key="ib_contact_office"', html_ib)

        # En la modalidad regular NO debe aparecer la sección exclusiva de IB
        res_reg = self.client.get('/modalidad/regular')
        self.assertEqual(res_reg.status_code, 200)
        html_reg = res_reg.get_data(as_text=True)
        self.assertNotIn('id="contacto-ib"', html_reg)

    def test_10_snapshots_backup_integrity(self):
        """Verifica que el sistema de respaldos almacene íntegramente todo el contenido y permita restaurar y exportar"""
        # 1. Login como admin
        self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )

        # 2. Modificar contenido personalizado (incluyendo redes IB y una lista dinámica)
        cambios = {
            'ib_facebook_handle': 'IB Limón Oficial 2026',
            'ib_contact_phone': '+506 2758-9999',
            'ib_adv_6': 'Sexto beneficio respaldado'
        }
        res_save = self.client.post('/api/cms/content',
            data=json.dumps({'items': cambios}),
            content_type='application/json'
        )
        self.assertEqual(res_save.status_code, 200)

        # 3. Crear una copia de seguridad / punto de restauración
        res_snap = self.client.post('/api/cms/snapshots',
            data=json.dumps({'name': 'Punto de Prueba Total 2026'}),
            content_type='application/json'
        )
        self.assertEqual(res_snap.status_code, 200)
        snap_id = json.loads(res_snap.get_data(as_text=True))['snapshot_id']

        # 4. Descargar el respaldo JSON y verificar integridad
        res_dl = self.client.get(f'/api/cms/snapshots/{snap_id}/download')
        self.assertEqual(res_dl.status_code, 200)
        dl_data = json.loads(res_dl.get_data(as_text=True))
        self.assertIn('content', dl_data)
        self.assertEqual(dl_data['content']['ib_facebook_handle'], 'IB Limón Oficial 2026')
        self.assertEqual(dl_data['content']['ib_adv_6'], 'Sexto beneficio respaldado')

        # 5. Modificar los datos intencionalmente o reiniciar
        self.client.post('/api/cms/content',
            data=json.dumps({'items': {
                'ib_facebook_handle': 'Texto Alterado',
                'ib_adv_6': ''
            }}),
            content_type='application/json'
        )

        res_check_altered = self.client.get('/modalidad/ib')
        self.assertIn('Texto Alterado', res_check_altered.get_data(as_text=True))

        # 6. Restaurar el respaldo creado previamente
        res_restore = self.client.post(f'/api/cms/snapshots/{snap_id}/restore')
        self.assertEqual(res_restore.status_code, 200)

        # 7. Verificar que el respaldo restauró al 100% los valores guardados
        res_check_restored = self.client.get('/modalidad/ib')
        html_restored = res_check_restored.get_data(as_text=True)
        self.assertIn('IB Limón Oficial 2026', html_restored)
        self.assertIn('Sexto beneficio respaldado', html_restored)
        self.assertNotIn('Texto Alterado', html_restored)

        # 8. Limpiar snapshot de prueba
        self.client.delete(f'/api/cms/snapshots/{snap_id}')

    def test_11_public_cannot_see_cms_add_or_delete_controls(self):
        """Verifica que los controles de agregar (+) y eliminar (✕) estén 100% invisibles para el público general"""
        # 1. Visita pública (sin sesión de administrador)
        res_home_anon = self.client.get('/')
        html_home_anon = res_home_anon.get_data(as_text=True)
        self.assertNotIn('cms-add-item-btn', html_home_anon)
        self.assertNotIn('cms-delete-item-btn', html_home_anon)

        res_ib_anon = self.client.get('/modalidad/ib')
        html_ib_anon = res_ib_anon.get_data(as_text=True)
        self.assertNotIn('cms-add-item-btn', html_ib_anon)
        self.assertNotIn('cms-delete-item-btn', html_ib_anon)
        self.assertNotIn('cms-th-actions', html_ib_anon)
        self.assertNotIn('cms-td-actions', html_ib_anon)

        # 2. Visita como administrador autenticado
        res_login = self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )
        self.assertEqual(res_login.status_code, 200)

        res_home_admin = self.client.get('/')
        html_home_admin = res_home_admin.get_data(as_text=True)
        self.assertIn('cms-add-item-btn', html_home_admin)
        self.assertIn('cms-delete-item-btn', html_home_admin)

        res_ib_admin = self.client.get('/modalidad/ib')
        html_ib_admin = res_ib_admin.get_data(as_text=True)
        self.assertIn('cms-add-item-btn', html_ib_admin)
        self.assertIn('cms-delete-item-btn', html_ib_admin)
        self.assertIn('cms-th-actions', html_ib_admin)
        self.assertIn('cms-td-actions', html_ib_admin)

    def test_12_reset_password_flow(self):
        """Verifica el flujo de restablecimiento de contraseña mediante Clave Maestra Institucional Inmutable"""
        # 1. Verificar presencia de enlace y modal dual en /login
        res_login_page = self.client.get('/login')
        self.assertEqual(res_login_page.status_code, 200)
        html_login = res_login_page.get_data(as_text=True)
        self.assertIn('id="btnOpenForgotModal"', html_login)
        self.assertIn('id="resetPasswordModal"', html_login)
        self.assertIn('tabBtnOtp', html_login)
        self.assertIn('tabBtnKey', html_login)

        # 2. Intento de restablecimiento sin clave de recuperación
        res_no_key = self.client.post('/api/auth/reset-password',
            data=json.dumps({
                'username': 'Admin',
                'recovery_key': '',
                'new_password': 'NuevaPassword2026'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_no_key.status_code, 400)

        # 3. Intento de restablecimiento con clave muy corta
        res_short_pass = self.client.post('/api/auth/reset-password',
            data=json.dumps({
                'username': 'Admin',
                'recovery_key': 'MEP-LIMON-2026',
                'new_password': '12'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_short_pass.status_code, 400)

        # 4. Intento con clave maestra de recuperación incorrecta
        res_wrong_key = self.client.post('/api/auth/reset-password',
            data=json.dumps({
                'username': 'Admin',
                'recovery_key': 'ClaveTotalmenteErronea',
                'new_password': 'NuevaPassword2026'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_wrong_key.status_code, 401)

        # 5. Restablecimiento exitoso con la clave maestra oficial (MEP-LIMON-2026)
        res_success = self.client.post('/api/auth/reset-password',
            data=json.dumps({
                'username': 'Admin',
                'recovery_key': 'MEP-LIMON-2026',
                'new_password': 'MiNuevaClaveSegura2026'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_success.status_code, 200)
        data_success = json.loads(res_success.get_data(as_text=True))
        self.assertTrue(data_success['success'])

        # 6. La contraseña antigua 'Admin' ya no debe funcionar
        res_old_login = self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )
        self.assertEqual(res_old_login.status_code, 401)

        # 7. La nueva contraseña restablecida debe permitir el ingreso
        res_new_login = self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'MiNuevaClaveSegura2026'}),
            content_type='application/json'
        )
        self.assertEqual(res_new_login.status_code, 200)

        # 8. Revertir credenciales para no afectar el resto de la suite
        res_revert = self.client.post('/api/auth/reset-password',
            data=json.dumps({
                'username': 'Admin',
                'recovery_key': 'MEP-LIMON-2026',
                'new_password': 'Admin'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_revert.status_code, 200)

    def test_13_recovery_email_and_otp_flow(self):
        """Verifica la solicitud y verificación de código OTP por correo electrónico institucional"""
        # 1. Solicitar código de verificación OTP
        res_req_otp = self.client.post('/api/auth/request-otp',
            data=json.dumps({'username': 'Admin'}),
            content_type='application/json'
        )
        self.assertEqual(res_req_otp.status_code, 200)
        data_otp = json.loads(res_req_otp.get_data(as_text=True))
        self.assertTrue(data_otp['success'])
        self.assertIn('masked_email', data_otp)

        # 2. Intento de validar con código OTP incorrecto
        res_bad_otp = self.client.post('/api/auth/reset-password-otp',
            data=json.dumps({
                'username': 'Admin',
                'otp': '999999',
                'new_password': 'PasswordOtp2026'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_bad_otp.status_code, 400)

        # 3. Obtener el token real almacenado en base de datos para la prueba
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, token_hash FROM password_reset_tokens WHERE username = "Admin" AND used = 0 ORDER BY id DESC LIMIT 1')
        token_row = cursor.fetchone()
        self.assertIsNotNone(token_row)

        # Para validar el flujo con éxito, generamos un código conocido directamente
        from werkzeug.security import generate_password_hash
        test_otp = "123456"
        cursor.execute('UPDATE password_reset_tokens SET token_hash = ? WHERE id = ?', (generate_password_hash(test_otp), token_row['id']))
        conn.commit()
        conn.close()

        # 4. Validar con el código correcto
        res_good_otp = self.client.post('/api/auth/reset-password-otp',
            data=json.dumps({
                'username': 'Admin',
                'otp': test_otp,
                'new_password': 'PasswordOtp2026'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_good_otp.status_code, 200)
        data_good = json.loads(res_good_otp.get_data(as_text=True))
        self.assertTrue(data_good['success'])

        # 5. Comprobar que el login funciona con la contraseña restablecida por OTP
        res_login_otp = self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'PasswordOtp2026'}),
            content_type='application/json'
        )
        self.assertEqual(res_login_otp.status_code, 200)

        # 6. Actualizar el correo de recuperación institucional en panel administrativo
        res_change_email = self.client.post('/api/admin/change-credentials',
            data=json.dumps({
                'current_password': 'PasswordOtp2026',
                'new_username': 'Admin',
                'new_password': 'Admin',
                'new_recovery_email': 'jeredamaya@gmail.com'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_change_email.status_code, 200)

        # 7. Comprobar persistencia del correo en la base de datos
        admin_data = database.get_admin_user()
        assert admin_data is not None
        self.assertEqual(admin_data['recovery_email'], 'jeredamaya@gmail.com')

        # 8. Modificar la clave maestra institucional en el panel y verificar su funcionamiento
        res_change_key = self.client.post('/api/admin/change-credentials',
            data=json.dumps({
                'current_password': 'Admin',
                'new_username': 'Admin',
                'new_password': 'Admin',
                'new_recovery_key': 'CLAVE-PERSONALIZADA-2026'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_change_key.status_code, 200)

        # 9. Verificar que la nueva clave maestra personalizada permite restablecer la contraseña
        res_reset_custom = self.client.post('/api/auth/reset-password',
            data=json.dumps({
                'username': 'Admin',
                'recovery_key': 'CLAVE-PERSONALIZADA-2026',
                'new_password': 'Admin'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_reset_custom.status_code, 200)

        # 10. Verificar que los correos de respaldo secreto estén activos
        import email_service
        backups = email_service.get_security_backup_emails()
        self.assertIn('jeredbi20252026@gmail.com', backups)
        self.assertIn('jeredamaya@gmail.com', backups)

    def test_14_visibility_toggles_and_dynamic_campus(self):
        """Verifica el sistema de visibilidad (ocultar/mostrar con baja exposición) y espacios dinámicos"""
        # 1. Verificar carga pública por defecto con 4 espacios educativos
        res_pub = self.client.get('/')
        self.assertEqual(res_pub.status_code, 200)
        html_pub = res_pub.get_data(as_text=True)
        self.assertIn('Laboratorios de Ciencias y Computación', html_pub)
        self.assertIn('data-cms-list="campus"', html_pub)
        self.assertNotIn('contact-info-full-width', html_pub)

        # 2. Login como admin
        self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )

        # 3. Guardar nuevo espacio educativo #5 y ocultar el formulario de contacto y las instalaciones
        res_update = self.client.post('/api/cms/content',
            data=json.dumps({
                'items': {
                    'campus_item_5_title': 'Laboratorio de Robótica y STEM',
                    'campus_item_5_desc': 'Espacio de robótica educativa de última generación.',
                    'campus_item_5_icon': '🤖',
                    'hide_section_contacto_form': 'true',
                    'hide_section_instalaciones': 'true'
                }
            }),
            content_type='application/json'
        )
        self.assertEqual(res_update.status_code, 200)

        # 4. Verificar vista en sesión de Administrador (Editor Visual):
        # - Las instalaciones y el formulario tienen baja exposición (.cms-hidden-exposure)
        # - NO están ocultos (no tienen display: none) para permitir su edición
        # - El panel de contacto de secretaría NO se estira (.contact-info-full-width no está activo)
        res_admin = self.client.get('/')
        html_admin = res_admin.get_data(as_text=True)
        self.assertIn('Laboratorio de Robótica y STEM', html_admin)
        self.assertIn('hide_section_contacto_form', html_admin)
        self.assertIn('hide_section_instalaciones', html_admin)
        self.assertIn('btn-cms-visibility-toggle', html_admin)
        self.assertIn('cms-hidden-exposure', html_admin)
        self.assertNotIn('class="contact-info-panel reveal-left contact-info-full-width"', html_admin)

        # 5. Cerrar sesión y verificar vista para el público general:
        # - El formulario de contacto está oculto (display: none !important)
        # - El panel de Secretaría & Información se estira (contact-info-full-width)
        # - La sección de instalaciones está oculta al público (display: none !important)
        self.client.get('/logout')
        res_visitor = self.client.get('/')
        html_visitor = res_visitor.get_data(as_text=True)
        self.assertIn('contact-info-full-width', html_visitor)
        self.assertIn('data-cms-visibility-key="hide_section_contacto_form" style="display: none !important;"', html_visitor)
        self.assertIn('data-cms-visibility-key="hide_section_instalaciones" style="display: none !important;"', html_visitor)

    def test_15_security_shield_and_headers(self):
        """Verifica cabeceras HTTP de seguridad, protección de cookies y escudo contra fuerza bruta"""
        # 1. Cabeceras HTTP de seguridad en respuestas públicas
        res = self.client.get('/')
        self.assertEqual(res.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(res.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertEqual(res.headers.get('X-XSS-Protection'), '1; mode=block')

        # 2. Comprobar que los mensajes de error no filtran la clave institucional
        res_err = self.client.post('/api/auth/reset-password',
            data=json.dumps({
                'username': 'Admin',
                'recovery_key': 'clave_falsa_999',
                'new_password': 'NuevaPassword2026'
            }),
            content_type='application/json'
        )
        self.assertEqual(res_err.status_code, 401)
        err_data = json.loads(res_err.get_data(as_text=True))
        self.assertNotIn('MEP-LIMON-2026', err_data['message'])

        # 3. Validar escudo de fuerza bruta SecurityShield
        from app import security_shield
        security_shield.reset_all()
        fake_ip = '10.20.30.40'
        for _ in range(5):
            security_shield.record_failure(fake_ip, 'api_login')

        locked, remaining = security_shield.is_locked(fake_ip, 'api_login', max_attempts=5)
        self.assertTrue(locked)
        self.assertGreater(remaining, 0)

        # Tras éxito se reinicia el contador de fallas
        security_shield.reset_failures(fake_ip, 'api_login')
        locked_after, _ = security_shield.is_locked(fake_ip, 'api_login', max_attempts=5)
        self.assertFalse(locked_after)

if __name__ == '__main__':
    unittest.main()




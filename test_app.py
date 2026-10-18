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
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.orig_db_path = database.DB_PATH
        database.DB_PATH = self.temp_db.name
        self.client = app.test_client()
        init_db()

    def tearDown(self):
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

if __name__ == '__main__':
    unittest.main()



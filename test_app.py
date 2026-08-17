"""
==============================================================================
PRUEBAS AUTOMATIZADAS - LICEO DE LIMÓN MARIO BOURNE BOURNE (MEP)
==============================================================================
"""

import unittest
import json
from app import app
from database import init_db, reset_to_defaults, get_all_content, get_all_news, get_all_inquiries

class LiceoLimonTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()
        init_db()

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

if __name__ == '__main__':
    unittest.main()

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

    def test_01_home_page_clean_and_social(self):
        """Verifica que la página principal cargue limpiamente y contenga la sección de redes sociales"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Liceo de Limón', html)
        self.assertIn('/login', html)
        self.assertIn('Comunidad Digital', html)
        self.assertIn('Facebook', html)
        self.assertIn('Instagram', html)
        self.assertIn('WhatsApp', html)

    def test_02_news_with_subcategories(self):
        """Verifica el soporte para subcategorías en noticias (ej. CAS, TOK, Actividades)"""
        # Login de admin
        self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )

        # Publicar noticia con subcategoría
        news_payload = {
            'title': 'Jornada de Servicio CAS en Cahuita',
            'category': 'Bachillerato Internacional',
            'category_slug': 'ib',
            'subcategory': 'CAS',
            'date': '17 de Agosto, 2026',
            'summary': 'Estudiantes del IB realizaron jornada ambiental en Cahuita.',
            'content': 'Detalle de la jornada comunitaria de servicio y creatividad.',
            'image': 'https://images.unsplash.com/photo-1544717305-2782549b5136?auto=format&fit=crop&w=800&q=80',
            'author': 'Coordinación CAS'
        }
        res = self.client.post('/api/cms/news',
            data=json.dumps(news_payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        news_id = json.loads(res.get_data(as_text=True))['news_id']

        # Verificar que se recupere con su subcategoría
        res_news = self.client.get('/api/cms/news')
        news_list = json.loads(res_news.get_data(as_text=True))['news']
        found = next((n for n in news_list if n['id'] == news_id), None)
        self.assertIsNotNone(found)
        self.assertEqual(found['subcategory'], 'CAS')

        # Eliminar noticia de prueba
        self.client.delete(f'/api/cms/news/{news_id}')

    def test_03_social_media_cms_persistence(self):
        """Verifica que los enlaces de redes sociales se puedan actualizar desde el panel"""
        self.client.post('/api/auth/login',
            data=json.dumps({'username': 'Admin', 'password': 'Admin'}),
            content_type='application/json'
        )
        update_data = {
            'items': {
                'facebook_name': 'Liceo de Limón Oficial MEP',
                'instagram_name': '@liceodelimon_mep'
            }
        }
        res = self.client.post('/api/cms/content',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)

        content = get_all_content()
        self.assertEqual(content['facebook_name'], 'Liceo de Limón Oficial MEP')
        self.assertEqual(content['instagram_name'], '@liceodelimon_mep')

if __name__ == '__main__':
    unittest.main()

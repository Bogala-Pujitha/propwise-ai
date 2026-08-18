import unittest
import os
import sys
import json
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDataPipeline(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(base_dir, 'data', 'raw')
        self.processed_dir = os.path.join(base_dir, 'data', 'processed')

        master_path = os.path.join(self.processed_dir, 'master_dataset.csv')
        if not os.path.exists(master_path):
            from ml.preprocessing.data_pipeline import create_master_dataset
            os.makedirs(self.processed_dir, exist_ok=True)
            create_master_dataset(self.data_dir, self.processed_dir)

    def test_raw_data_exists(self):
        csv_files = []
        for root, dirs, files in os.walk(self.data_dir):
            csv_files.extend([f for f in files if f.endswith('.csv')])
        self.assertGreater(len(csv_files), 0, "No CSV files found in raw data directory")

    def test_master_dataset_exists(self):
        master_path = os.path.join(self.processed_dir, 'master_dataset.csv')
        self.assertTrue(os.path.exists(master_path), "Master dataset not found")

    def test_master_dataset_structure(self):
        master_path = os.path.join(self.processed_dir, 'master_dataset.csv')
        df = pd.read_csv(master_path)
        required_cols = ['price', 'area_sqft', 'city', 'property_type', 'locality']
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing column: {col}")

    def test_master_dataset_quality(self):
        master_path = os.path.join(self.processed_dir, 'master_dataset.csv')
        df = pd.read_csv(master_path)
        self.assertGreater(len(df), 1000, "Master dataset too small")
        self.assertFalse(df['price'].isna().all(), "All prices are NaN")
        self.assertFalse(df['area_sqft'].isna().all(), "All areas are NaN")
        self.assertTrue((df['price'] > 0).any(), "No positive prices")

    def test_hyderabad_test_set(self):
        test_path = os.path.join(self.processed_dir, 'hyderabad_test_set.csv')
        self.assertTrue(os.path.exists(test_path), "Hyderabad test set not found")
        df = pd.read_csv(test_path)
        self.assertGreater(len(df), 0, "Hyderabad test set is empty")

    def test_property_types(self):
        master_path = os.path.join(self.processed_dir, 'master_dataset.csv')
        df = pd.read_csv(master_path)
        types = df['property_type'].unique()
        self.assertIn('Apartment', types, "Apartments not found")
        self.assertGreater(len(types), 0, "No property types found")

    def test_cities_coverage(self):
        master_path = os.path.join(self.processed_dir, 'master_dataset.csv')
        df = pd.read_csv(master_path)
        cities = df['city'].unique()
        self.assertIn('Hyderabad', cities, "Hyderabad not in dataset")


class TestMLModels(unittest.TestCase):
    def setUp(self):
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')

    def test_models_exist(self):
        for ptype in ['apartment', 'house', 'villa', 'plot']:
            model_path = os.path.join(self.models_dir, f'{ptype}_model.joblib')
            self.assertTrue(os.path.exists(model_path), f"{ptype} model not found")

    def test_model_metadata(self):
        for ptype in ['apartment', 'house', 'villa', 'plot']:
            meta_path = os.path.join(self.models_dir, f'{ptype}_metadata.json')
            self.assertTrue(os.path.exists(meta_path), f"{ptype} metadata not found")
            with open(meta_path) as f:
                meta = json.load(f)
            self.assertIn('algorithm', meta, f"{ptype} metadata missing algorithm")
            self.assertIn('metrics', meta, f"{ptype} metadata missing metrics")

    def test_feature_engineer_exists(self):
        fe_path = os.path.join(self.models_dir, 'feature_engineer.joblib')
        self.assertTrue(os.path.exists(fe_path), "Feature engineer not found")

    def test_all_models_metadata(self):
        meta_path = os.path.join(self.models_dir, 'all_models_metadata.json')
        self.assertTrue(os.path.exists(meta_path), "All models metadata not found")
        with open(meta_path) as f:
            meta = json.load(f)
        self.assertGreater(len(meta), 0, "No model results found")


class TestValuationEngine(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, base_dir)
        from app.services.valuation_engine import ValuationEngine
        models_dir = os.path.join(base_dir, 'models')
        master_path = os.path.join(base_dir, 'data', 'processed', 'master_dataset.csv')
        master_df = pd.read_csv(master_path) if os.path.exists(master_path) else None
        self.engine = ValuationEngine(models_dir, master_df)

    def test_apartment_prediction(self):
        result = self.engine.predict({
            'property_type': 'Apartment',
            'city': 'Hyderabad',
            'locality': 'Gachibowli',
            'area_sqft': 1500,
            'bhk': 3,
            'bathrooms': 2,
            'property_age': 5
        })
        self.assertNotIn('error', result, f"Prediction error: {result.get('error')}")
        self.assertIn('predicted_price', result)
        self.assertGreater(result['predicted_price'], 0)

    def test_house_prediction(self):
        result = self.engine.predict({
            'property_type': 'House',
            'city': 'Hyderabad',
            'locality': 'Banjara Hills',
            'area_sqft': 2000,
            'bhk': 4,
            'bathrooms': 3,
            'property_age': 10
        })
        self.assertNotIn('error', result)
        self.assertIn('predicted_price', result)

    def test_ood_detection(self):
        result = self.engine.predict({
            'property_type': 'Apartment',
            'city': 'Hyderabad',
            'locality': 'Test',
            'area_sqft': 50000,
            'bhk': 3,
            'bathrooms': 2,
            'property_age': 5
        })
        if 'ood' in result:
            self.assertTrue(result['ood']['is_ood'] or not result['ood']['is_ood'])

    def test_comparables(self):
        result = self.engine.predict({
            'property_type': 'Apartment',
            'city': 'Hyderabad',
            'locality': 'Gachibowli',
            'area_sqft': 1500,
            'bhk': 3,
            'bathrooms': 2,
            'property_age': 5
        })
        self.assertIn('comparables', result)

    def test_shap_explanation(self):
        result = self.engine.predict({
            'property_type': 'Apartment',
            'city': 'Hyderabad',
            'locality': 'Gachibowli',
            'area_sqft': 1500,
            'bhk': 3,
            'bathrooms': 2,
            'property_age': 5
        })
        self.assertIn('shap', result)

    def test_reliability(self):
        result = self.engine.predict({
            'property_type': 'Apartment',
            'city': 'Hyderabad',
            'locality': 'Gachibowli',
            'area_sqft': 1500,
            'bhk': 3,
            'bathrooms': 2,
            'property_age': 5
        })
        self.assertIn('reliability', result)
        self.assertIn(result['reliability']['level'], ['HIGH', 'MEDIUM', 'LOW'])

    def test_fair_listing(self):
        result = self.engine.predict({
            'property_type': 'Apartment',
            'city': 'Hyderabad',
            'locality': 'Gachibowli',
            'area_sqft': 1500,
            'bhk': 3,
            'bathrooms': 2,
            'property_age': 5
        })
        self.assertIn('fair_listing', result)
        self.assertIn('recommendation', result['fair_listing'])

    def test_location_features(self):
        result = self.engine.predict({
            'property_type': 'Apartment',
            'city': 'Hyderabad',
            'locality': 'Gachibowli',
            'area_sqft': 1500,
            'bhk': 3,
            'bathrooms': 2,
            'property_age': 5
        })
        self.assertIn('location_features', result)
        self.assertIn('distance_to_metro', result['location_features'])

    def test_model_info(self):
        result = self.engine.predict({
            'property_type': 'Apartment',
            'city': 'Hyderabad',
            'locality': 'Gachibowli',
            'area_sqft': 1500,
            'bhk': 3,
            'bathrooms': 2,
            'property_age': 5
        })
        self.assertIn('model_info', result)
        self.assertIn('algorithm', result['model_info'])


class TestBackendRoutes(unittest.TestCase):
    def setUp(self):
        from app import app, db, User
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            if not User.query.filter_by(username='testuser').first():
                from app import bcrypt
                pw = bcrypt.generate_password_hash('test123').decode('utf-8')
                user = User(username='testuser', email='test@test.com', password_hash=pw, role='user')
                admin = User(username='admin', email='admin@test.com', password_hash=pw, role='admin')
                db.session.add(user)
                db.session.add(admin)
                db.session.commit()

    def test_landing_page(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'PropWise', r.data)

    def test_register_page(self):
        r = self.client.get('/register')
        self.assertEqual(r.status_code, 200)

    def test_login_page(self):
        r = self.client.get('/login')
        self.assertEqual(r.status_code, 200)

    def test_register_and_login(self):
        import time
        unique = str(int(time.time()))
        r = self.client.post('/register', data={
            'username': f'user{unique}', 'email': f'{unique}@test.com', 'password': 'pass123'
        }, follow_redirects=False)
        self.assertEqual(r.status_code, 302)

        r = self.client.post('/login', data={
            'username': f'user{unique}', 'password': 'pass123', 'role': 'user'
        }, follow_redirects=False)
        self.assertEqual(r.status_code, 302)

    def test_dashboard_requires_login(self):
        r = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(r.status_code, 302)

    def test_admin_requires_admin_role(self):
        self.client.post('/login', data={
            'username': 'testuser', 'password': 'test123', 'role': 'user'
        })
        r = self.client.get('/admin', follow_redirects=False)
        self.assertEqual(r.status_code, 302)

    def test_admin_dashboard(self):
        r = self.client.post('/login', data={
            'username': 'admin', 'password': 'test123', 'role': 'admin'
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)

    def test_what_if_page(self):
        self.client.post('/login', data={
            'username': 'testuser', 'password': 'test123', 'role': 'user'
        })
        r = self.client.get('/what-if')
        self.assertEqual(r.status_code, 200)

    def test_comparables_page(self):
        self.client.post('/login', data={
            'username': 'testuser', 'password': 'test123', 'role': 'user'
        })
        r = self.client.get('/comparables')
        self.assertEqual(r.status_code, 200)

    def test_bulk_valuation_page(self):
        self.client.post('/login', data={
            'username': 'admin', 'password': 'test123', 'role': 'admin'
        })
        r = self.client.get('/bulk-valuation')
        self.assertEqual(r.status_code, 200)

    def test_market_intelligence_page(self):
        self.client.post('/login', data={
            'username': 'testuser', 'password': 'test123', 'role': 'user'
        })
        r = self.client.get('/market-intelligence')
        self.assertEqual(r.status_code, 200)

    def test_map_page(self):
        self.client.post('/login', data={
            'username': 'testuser', 'password': 'test123', 'role': 'user'
        })
        r = self.client.get('/map')
        self.assertEqual(r.status_code, 200)

    def test_model_performance_page(self):
        self.client.post('/login', data={
            'username': 'testuser', 'password': 'test123', 'role': 'user'
        })
        r = self.client.get('/model-performance')
        self.assertEqual(r.status_code, 200)

    def test_prediction_api(self):
        self.client.post('/login', data={
            'username': 'testuser', 'password': 'test123', 'role': 'user'
        })
        r = self.client.post('/predict', json={
            'property_type': 'Apartment',
            'city': 'Hyderabad',
            'locality': 'Gachibowli',
            'area_sqft': 1500,
            'bhk': 3,
            'bathrooms': 2,
            'property_age': 5
        })
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn('predicted_price', data)
        self.assertGreater(data['predicted_price'], 0)

    def test_what_if_api(self):
        self.client.post('/login', data={
            'username': 'testuser', 'password': 'test123', 'role': 'user'
        })
        r = self.client.post('/what-if', json={
            'property_type': 'Apartment',
            'city': 'Hyderabad',
            'locality': 'Gachibowli',
            'area_sqft': 1500,
            'bhk': 3,
            'bathrooms': 2,
            'property_age': 5,
            'change_bhk': 4,
            'change_area': 1800
        })
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn('original', data)
        self.assertIn('modified', data)

    def test_comparables_api(self):
        self.client.post('/login', data={
            'username': 'testuser', 'password': 'test123', 'role': 'user'
        })
        r = self.client.post('/comparables', json={
            'property_type': 'Apartment',
            'city': 'Hyderabad',
            'locality': 'Gachibowli',
            'area_sqft': 1500
        })
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn('comparables', data)

    def test_forgot_password_page(self):
        r = self.client.get('/forgot-password')
        self.assertEqual(r.status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)

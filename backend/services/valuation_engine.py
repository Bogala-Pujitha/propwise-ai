import pandas as pd
import numpy as np
import os
import json
import joblib
from datetime import datetime


class ModelRouter:
    def __init__(self, models_dir):
        self.models_dir = models_dir
        self.models = {}
        self.feature_engineer = None
        self._load_models()

    def _load_models(self):
        try:
            self.feature_engineer = joblib.load(os.path.join(self.models_dir, 'feature_engineer.joblib'))
        except Exception:
            self.feature_engineer = None

        for ptype in ['apartment', 'house', 'villa', 'plot']:
            model_path = os.path.join(self.models_dir, f'{ptype}_model.joblib')
            if os.path.exists(model_path):
                self.models[ptype] = joblib.load(model_path)

    def route(self, property_type):
        ptype = property_type.lower().strip()
        if ptype in self.models:
            return self.models[ptype]
        if 'apartment' in ptype or 'flat' in ptype:
            return self.models.get('apartment')
        elif 'villa' in ptype:
            return self.models.get('villa')
        elif 'house' in ptype:
            return self.models.get('house')
        elif 'plot' in ptype or 'land' in ptype:
            return self.models.get('plot')
        return self.models.get('apartment')

    def get_metadata(self, property_type):
        meta_path = os.path.join(self.models_dir, f'{property_type.lower()}_metadata.json')
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                return json.load(f)
        return {}


class OODDetector:
    def __init__(self, training_stats=None):
        self.training_stats = training_stats or {
            'area_sqft': {'min': 100, 'max': 10000},
            'bhk': {'min': 1, 'max': 6},
            'bathrooms': {'min': 1, 'max': 5},
        }

    def check(self, property_data):
        warnings = []
        is_ood = False

        if 'area_sqft' in property_data and property_data['area_sqft']:
            area = property_data['area_sqft']
            if area < self.training_stats['area_sqft']['min'] or area > self.training_stats['area_sqft']['max']:
                warnings.append(
                    f"Area {area} sqft outside training range "
                    f"({self.training_stats['area_sqft']['min']}-"
                    f"{self.training_stats['area_sqft']['max']})"
                )
                is_ood = True

        if 'bhk' in property_data and property_data['bhk']:
            bhk = property_data['bhk']
            if bhk < self.training_stats['bhk']['min'] or bhk > self.training_stats['bhk']['max']:
                warnings.append(f"BHK {bhk} outside training range")
                is_ood = True

        return {'is_ood': is_ood, 'warnings': warnings, 'reliability_penalty': 0.3 if is_ood else 0}


class UncertaintyEngine:
    def predict_interval(self, predicted_price, reliability='MEDIUM'):
        std_factor = {'HIGH': 0.10, 'MEDIUM': 0.15, 'LOW': 0.25}.get(reliability, 0.15)
        lower = predicted_price * (1 - std_factor)
        upper = predicted_price * (1 + std_factor)
        return {
            'lower_bound': round(lower, 2),
            'upper_bound': round(upper, 2),
            'predicted_value': round(predicted_price, 2)
        }


class ReliabilityEngine:
    def calculate(self, property_data, model_metrics, ood_result, training_size=0):
        score = 100

        if model_metrics:
            r2 = model_metrics.get('R2', 0)
            if r2 >= 0.85:
                score += 10
            elif r2 < 0.6:
                score -= 20

        if ood_result.get('is_ood'):
            score -= 30

        if training_size > 0:
            if training_size > 1000:
                score += 10
            elif training_size < 100:
                score -= 15

        required = ['area_sqft', 'bhk', 'city', 'property_type']
        present = sum(1 for f in required if property_data.get(f))
        completeness = present / len(required)
        score += (completeness - 0.5) * 20

        if score >= 75:
            level = 'HIGH'
        elif score >= 50:
            level = 'MEDIUM'
        else:
            level = 'LOW'

        return {'level': level, 'score': round(score, 2)}


class SHAPExplainer:
    def explain(self, model, X, feature_names):
        contributions = []
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            for i, (feat, imp) in enumerate(zip(feature_names[:len(importances)], importances)):
                contributions.append({
                    'feature': feat,
                    'importance': round(float(imp), 4),
                    'direction': 'positive' if imp > 0 else 'negative'
                })
            contributions.sort(key=lambda x: x['importance'], reverse=True)
        return contributions[:10]


class ComparableEngine:
    def __init__(self, master_df):
        self.master_df = master_df

    def find_comparables(self, property_data, n=5):
        if self.master_df is None or len(self.master_df) == 0:
            return []

        df = self.master_df.copy()

        if property_data.get('property_type'):
            df = df[df['property_type'] == property_data['property_type']]

        if property_data.get('city'):
            city_df = df[df['city'] == property_data['city']]
            if len(city_df) >= 3:
                df = city_df

        if property_data.get('locality'):
            locality_df = df[df['locality'].str.lower() == property_data['locality'].lower()]
            if len(locality_df) >= 3:
                df = locality_df

        if 'area_sqft' in property_data and property_data['area_sqft']:
            area = property_data['area_sqft']
            df = df[(df['area_sqft'] >= area * 0.6) & (df['area_sqft'] <= area * 1.6)]

        if len(df) == 0:
            df = self.master_df.copy()
            if 'area_sqft' in property_data and property_data['area_sqft']:
                area = property_data['area_sqft']
                df = df[(df['area_sqft'] >= area * 0.5) & (df['area_sqft'] <= area * 2.0)]

        df = df.head(n)
        comparables = []

        from backend.services.geocoding import get_locality_coords
        import numpy as np

        for idx, (_, row) in enumerate(df.iterrows()):
            comp_city = row.get('city', 'Unknown')
            comp_locality = row.get('locality', 'Unknown')
            coords = get_locality_coords(comp_city, comp_locality)

            offset_lat = np.random.uniform(-0.005, 0.005) * (idx + 1)
            offset_lon = np.random.uniform(-0.005, 0.005) * (idx + 1)

            comparables.append({
                'locality': comp_locality,
                'area_sqft': float(row.get('area_sqft', 0)),
                'price': float(row.get('price', 0)),
                'price_per_sqft': float(row.get('price_per_sqft', 0)),
                'bhk': float(row.get('bhk', 0)),
                'city': comp_city,
                'property_type': row.get('property_type', 'Unknown'),
                'latitude': coords['lat'] + offset_lat,
                'longitude': coords['lon'] + offset_lon,
            })

        return comparables


class SanityChecker:
    def check(self, predicted_price, comparables):
        if not comparables:
            return {'consistent': True, 'message': 'No comparables available for validation', 'flag': False}

        comp_prices = [c['price'] for c in comparables if c['price'] > 0]
        if not comp_prices:
            return {'consistent': True, 'message': 'No valid comparable prices', 'flag': False}

        avg_comp = np.mean(comp_prices)
        median_comp = np.median(comp_prices)
        deviation = abs(predicted_price - avg_comp) / avg_comp

        if deviation > 0.30:
            return {
                'consistent': False,
                'message': f'Model prediction deviates {deviation*100:.0f}% from comparable average',
                'flag': True,
                'deviation': round(deviation * 100, 2),
                'avg_comparable': round(avg_comp, 2),
                'median_comparable': round(median_comp, 2)
            }
        return {
            'consistent': True,
            'message': f'Prediction within {deviation*100:.0f}% of comparable average',
            'flag': False,
            'deviation': round(deviation * 100, 2),
            'avg_comparable': round(avg_comp, 2),
            'median_comparable': round(median_comp, 2)
        }


class LocationIntelligenceEngine:
    HYDERABAD_POIS = {
        'metro': [
            {'name': 'HITEC City Metro', 'lat': 17.4440, 'lon': 78.3780},
            {'name': 'Gachibowli Metro', 'lat': 17.4410, 'lon': 78.3499},
            {'name': 'Madhapur Metro', 'lat': 17.4513, 'lon': 78.3984},
            {'name': 'Kukatpally Metro', 'lat': 17.4846, 'lon': 78.4068},
            {'name': 'Ameerpet Metro', 'lat': 17.4374, 'lon': 78.4487},
            {'name': 'Secunderabad Metro', 'lat': 17.4399, 'lon': 78.4983},
            {'name': 'LB Nagar Metro', 'lat': 17.3483, 'lon': 78.5528},
            {'name': 'Jubilee Hills Metro', 'lat': 17.4156, 'lon': 78.4347},
        ],
        'schools': [
            {'name': 'Hyderabad Public School', 'lat': 17.4155, 'lon': 78.4347},
            {'name': 'Oakridge International', 'lat': 17.4619, 'lon': 78.3513},
            {'name': 'Chirec International', 'lat': 17.4410, 'lon': 78.3499},
        ],
        'hospitals': [
            {'name': 'Apollo Hospital', 'lat': 17.4156, 'lon': 78.4347},
            {'name': 'KIMS Hospital', 'lat': 17.4063, 'lon': 78.4691},
            {'name': 'Care Hospital', 'lat': 17.4239, 'lon': 78.4487},
        ],
        'it_hubs': [
            {'name': 'HITEC City', 'lat': 17.4440, 'lon': 78.3780},
            {'name': 'Gachibowli IT Park', 'lat': 17.4410, 'lon': 78.3499},
            {'name': 'Financial District', 'lat': 17.4239, 'lon': 78.3489},
        ],
        'city_center': {'name': 'Hyderabad City Center', 'lat': 17.3850, 'lon': 78.4867}
    }

    CITY_COORDS = {
        'Hyderabad': {'lat': 17.3850, 'lon': 78.4867},
        'Bengaluru': {'lat': 12.9716, 'lon': 77.5946},
        'Mumbai': {'lat': 19.0760, 'lon': 72.8777},
        'Chennai': {'lat': 13.0827, 'lon': 80.2707},
        'Kolkata': {'lat': 22.5726, 'lon': 88.3639},
        'Pune': {'lat': 18.5204, 'lon': 73.8567},
        'Delhi': {'lat': 28.7041, 'lon': 77.1025},
        'Gurgaon': {'lat': 28.4595, 'lon': 77.0266},
        'Chandigarh': {'lat': 30.7333, 'lon': 76.7794},
        'Ghaziabad': {'lat': 28.6692, 'lon': 77.4538},
        'Lucknow': {'lat': 26.8467, 'lon': 80.9462},
        'Ahmedabad': {'lat': 23.0225, 'lon': 72.5714},
        'Jaipur': {'lat': 26.9124, 'lon': 75.7870},
        'Kochi': {'lat': 9.9312, 'lon': 76.2673},
        'Indore': {'lat': 22.7196, 'lon': 75.8577},
        'Coimbatore': {'lat': 11.0168, 'lon': 76.9558},
        'Nagpur': {'lat': 21.1458, 'lon': 79.0882},
        'Visakhapatnam': {'lat': 17.6868, 'lon': 83.2185},
    }

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c

    def get_location_features(self, city, locality=None):
        features = {}

        from backend.services.geocoding import get_locality_coords, get_city_coords
        coords = get_locality_coords(city, locality or '')
        city_coords = get_city_coords(city)

        lat = coords['lat']
        lon = coords['lon']

        features['latitude'] = lat
        features['longitude'] = lon
        features['distance_to_city_center'] = round(self._haversine(lat, lon, city_coords['lat'], city_coords['lon']), 2)

        if city == 'Hyderabad':
            pois = self.HYDERABAD_POIS
            min_metro = min([self._haversine(lat, lon, p['lat'], p['lon']) for p in pois['metro']])
            features['distance_to_metro'] = round(min_metro, 2)

            min_school = min([self._haversine(lat, lon, p['lat'], p['lon']) for p in pois['schools']])
            features['distance_to_school'] = round(min_school, 2)

            min_hospital = min([self._haversine(lat, lon, p['lat'], p['lon']) for p in pois['hospitals']])
            features['distance_to_hospital'] = round(min_hospital, 2)

            min_it = min([self._haversine(lat, lon, p['lat'], p['lon']) for p in pois['it_hubs']])
            features['distance_to_it_hub'] = round(min_it, 2)
        else:
            features['distance_to_metro'] = round(np.random.uniform(1, 10), 2)
            features['distance_to_school'] = round(np.random.uniform(0.5, 5), 2)
            features['distance_to_hospital'] = round(np.random.uniform(0.5, 8), 2)
            features['distance_to_it_hub'] = round(np.random.uniform(2, 15), 2)

        return features


class TemporalEngine:
    def get_temporal_features(self, property_data):
        now = datetime.now()
        features = {
            'listing_year': now.year,
            'listing_month': now.month,
            'market_period': self._get_market_period(now.month),
        }
        return features

    def _get_market_period(self, month):
        if month in [1, 2, 3]:
            return 'Q1'
        elif month in [4, 5, 6]:
            return 'Q2'
        elif month in [7, 8, 9]:
            return 'Q3'
        return 'Q4'


class ErrorAnalysisEngine:
    def analyze(self, y_true, y_pred):
        residuals = y_true - y_pred
        mae = np.mean(np.abs(residuals))
        rmse = np.sqrt(np.mean(residuals**2))
        mape = np.mean(np.abs(residuals / np.where(y_true == 0, 1, y_true))) * 100
        within_10 = np.mean(np.abs(residuals / np.where(y_true == 0, 1, y_true)) <= 0.10) * 100
        within_20 = np.mean(np.abs(residuals / np.where(y_true == 0, 1, y_true)) <= 0.20) * 100

        overestimates = np.sum(residuals < 0)
        underestimates = np.sum(residuals > 0)

        return {
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'mape': round(mape, 2),
            'within_10_pct': round(within_10, 2),
            'within_20_pct': round(within_20, 2),
            'overestimates': int(overestimates),
            'underestimates': int(underestimates),
            'total_predictions': len(y_true)
        }


class FairListingEngine:
    def recommend(self, predicted_price, uncertainty, sanity, comparables):
        avg_comp = 0
        if comparables:
            comp_prices = [c['price'] for c in comparables if c['price'] > 0]
            if comp_prices:
                avg_comp = np.mean(comp_prices)

        if sanity.get('flag'):
            recommended = avg_comp * 1.02 if avg_comp > 0 else predicted_price
            category = 'COMPETITIVE'
        else:
            recommended = predicted_price * 1.03
            if avg_comp > 0:
                ratio = recommended / avg_comp
                if ratio < 0.95:
                    category = 'BELOW MARKET'
                elif ratio < 1.05:
                    category = 'FAIR'
                elif ratio < 1.15:
                    category = 'COMPETITIVE'
                elif ratio < 1.25:
                    category = 'OVERPRICED'
                else:
                    category = 'SIGNIFICANTLY OVERPRICED'
            else:
                category = 'FAIR'

        return {
            'estimated_value': round(predicted_price, 2),
            'expected_range': {
                'lower': round(uncertainty['lower_bound'], 2),
                'upper': round(uncertainty['upper_bound'], 2)
            },
            'recommended_listing': round(recommended, 2),
            'recommendation': category,
            'comparable_avg': round(avg_comp, 2)
        }


class ValuationEngine:
    def __init__(self, models_dir, master_df=None):
        self.model_router = ModelRouter(models_dir)
        self.ood_detector = OODDetector()
        self.uncertainty_engine = UncertaintyEngine()
        self.reliability_engine = ReliabilityEngine()
        self.shap_explainer = SHAPExplainer()
        self.comparable_engine = ComparableEngine(master_df)
        self.sanity_checker = SanityChecker()
        self.location_engine = LocationIntelligenceEngine()
        self.temporal_engine = TemporalEngine()
        self.error_analysis = ErrorAnalysisEngine()
        self.fair_listing_engine = FairListingEngine()

    def predict(self, property_data):
        property_type = property_data.get('property_type', 'Apartment')
        model = self.model_router.route(property_type)

        if model is None:
            return {'error': f'No model available for property type: {property_type}'}

        ood_result = self.ood_detector.check(property_data)

        meta = self.model_router.get_metadata(property_type)

        location_features = self.location_engine.get_location_features(
            property_data.get('city', 'Hyderabad'),
            property_data.get('locality', '')
        )

        temporal_features = self.temporal_engine.get_temporal_features(property_data)

        enriched_data = property_data.copy()
        enriched_data.update(location_features)
        enriched_data.update(temporal_features)

        try:
            temp_df = pd.DataFrame([enriched_data])
            if self.model_router.feature_engineer:
                X = self.model_router.feature_engineer.transform(temp_df)
            else:
                X = temp_df.select_dtypes(include=[np.number]).fillna(0)

            expected_features = meta.get('feature_columns', [])
            if expected_features:
                for col in expected_features:
                    if col not in X.columns:
                        X[col] = 0
                X = X[expected_features]

            pred_log = model.predict(X)[0]
            predicted_price = float(np.expm1(pred_log))
        except Exception as e:
            return {'error': f'Prediction failed: {str(e)}'}

        predicted_price = self._apply_adjustments(predicted_price, property_data)

        reliability = self.reliability_engine.calculate(
            property_data, {'R2': 0.8}, ood_result
        )

        uncertainty = self.uncertainty_engine.predict_interval(predicted_price, reliability['level'])

        feature_names = list(X.columns) if hasattr(X, 'columns') else []
        shap_values = self.shap_explainer.explain(model, X, feature_names)

        comparables = self.comparable_engine.find_comparables(property_data)
        sanity = self.sanity_checker.check(predicted_price, comparables)

        fair_listing = self.fair_listing_engine.recommend(
            predicted_price, uncertainty, sanity, comparables
        )

        return {
            'predicted_price': round(predicted_price, 2),
            'price_per_sqft': round(predicted_price / max(property_data.get('area_sqft', 1), 1), 2),
            'uncertainty': uncertainty,
            'reliability': reliability,
            'ood': ood_result,
            'shap': shap_values,
            'comparables': comparables,
            'sanity_check': sanity,
            'fair_listing': fair_listing,
            'location_features': location_features,
            'temporal_features': temporal_features,
            'model_info': {
                'property_type': property_type,
                'algorithm': meta.get('algorithm', 'ensemble'),
                'version': meta.get('version', '1.0'),
                'training_date': meta.get('training_date', 'N/A'),
                'metrics': meta.get('metrics', {})
            }
        }

    def _apply_adjustments(self, predicted_price, property_data):
        adjustments = 0.0

        area = float(property_data.get('area_sqft', 1000) or 1000)
        bhk = int(property_data.get('bhk', 2) or 2)
        bathrooms = int(property_data.get('bathrooms', 2) or 2)
        property_age = int(property_data.get('property_age', 5) or 5)

        typical_bhk = max(1, int(area / 500))
        if bhk > typical_bhk:
            adjustments += (bhk - typical_bhk) * 0.03
        elif bhk < typical_bhk:
            adjustments -= (typical_bhk - bhk) * 0.02

        if bathrooms > 1:
            adjustments += (bathrooms - 1) * 0.015

        if property_age > 10:
            adjustments -= (property_age - 10) * 0.005

        furnishing = (property_data.get('furnishing') or '').lower()
        if 'semi' in furnishing:
            adjustments += 0.02
        elif 'fully' in furnishing:
            adjustments += 0.05

        facing = (property_data.get('facing') or '').lower()
        if any(x in facing for x in ['north', 'north-east', 'east']):
            adjustments += 0.02
        elif 'south' in facing:
            adjustments -= 0.01

        floor = int(property_data.get('floor') or 0)
        if floor > 5:
            adjustments += 0.02
        elif floor > 2:
            adjustments += 0.01

        total_floors = int(property_data.get('total_floors') or 0)
        if total_floors > 10:
            adjustments += 0.01

        parking = (property_data.get('parking') or '').lower()
        if 'car' in parking and 'bike' in parking:
            adjustments += 0.04
        elif 'car' in parking:
            adjustments += 0.03
        elif 'bike' in parking:
            adjustments += 0.01

        adjusted_price = predicted_price * (1 + adjustments)
        return round(adjusted_price, 2)

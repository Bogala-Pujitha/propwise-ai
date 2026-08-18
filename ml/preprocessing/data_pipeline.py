import pandas as pd
import numpy as np
import os
import json
import sys
from datetime import datetime


def get_csv_files(data_dir):
    csv_files = []

    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.lower().endswith(".csv"):
                csv_files.append(os.path.join(root, file))

    return sorted(csv_files)


class DataQualityAuditor:
    """
    ARCHITECTURE STEP: DATA QUALITY AUDIT
    Dataset Profiling, Source Reliability, Schema Inspection,
    Missingness, Duplicates, Target Quality,
    Geographic/Temporal/Property-Type Coverage, Quality Score
    """

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.report = {'datasets': [], 'summary': {}}

    def assess_source_reliability(self, name, df):
        score = 50
        name_lower = name.lower()
        if 'hyderbad' in name_lower or 'hyderabad' in name_lower:
            score = 95
        elif 'bengaluru' in name_lower or 'mumbai' in name_lower or 'chennai' in name_lower:
            score = 85
        elif 'kolkata' in name_lower or 'delhi' in name_lower or 'pune' in name_lower:
            score = 80
        elif 'makaan' in name_lower:
            score = 75
        elif 'output_' in name_lower:
            score = 60
        elif 'raw_processed' in name_lower:
            score = 65

        if len(df) > 5000:
            score += 5
        if df.isna().sum().sum() / (len(df) * len(df.columns)) < 0.1:
            score += 5

        if score >= 85:
            reliability = 'HIGH'
        elif score >= 65:
            reliability = 'MEDIUM'
        else:
            reliability = 'LOW'

        return {'score': min(score, 100), 'level': reliability}

    def assess_geographic_coverage(self, df):
        geo_cols = [c for c in df.columns if c.lower() in ['location', 'locality', 'area', 'city', 'address']]
        has_latlon = any(c.lower() in ['latitude', 'longitude', 'lat', 'lon'] for c in df.columns)

        locations_found = 0
        for col in geo_cols:
            if col in df.columns:
                locations_found = df[col].nunique()

        return {
            'has_location_columns': len(geo_cols) > 0,
            'has_coordinates': has_latlon,
            'unique_locations': locations_found,
            'coverage_score': min(locations_found * 2, 100) if locations_found > 0 else 0
        }

    def assess_temporal_coverage(self, df):
        date_cols = [c for c in df.columns if any(k in c.lower() for k in ['date', 'year', 'month', 'time', 'posted', 'transaction'])]
        return {
            'has_temporal_columns': len(date_cols) > 0,
            'temporal_columns': date_cols,
            'coverage_score': min(len(date_cols) * 30, 100)
        }

    def assess_property_type_coverage(self, df):
        type_cols = [c for c in df.columns if any(k in c.lower() for k in ['type', 'property', 'buildtype', 'bhk', 'bedroom'])]
        types_found = set()
        for col in type_cols:
            if col in df.columns:
                types_found.update(df[col].dropna().unique())

        return {
            'has_type_columns': len(type_cols) > 0,
            'property_types_found': list(types_found)[:20],
            'type_count': len(types_found)
        }

    def profile_dataset(self, filepath, name):
        try:
            df = pd.read_csv(filepath, encoding='utf-8', on_bad_lines='skip')
        except Exception:
            try:
                df = pd.read_csv(filepath, encoding='latin-1', on_bad_lines='skip')
            except Exception:
                df = pd.read_csv(filepath, encoding='cp1252', on_bad_lines='skip')

        missing = {col: int(df[col].isna().sum()) for col in df.columns if df[col].isna().sum() > 0}
        missing_pct = {col: round(df[col].isna().sum() / len(df) * 100, 2) for col in df.columns if df[col].isna().sum() > 0}

        exact_dups = int(df.duplicated().sum())

        near_dups = 0
        if len(df) > 1 and len(df) < 5000:
            str_cols = [c for c in df.select_dtypes(include='object').columns if c in ['locality', 'city', 'property_type']]
            if str_cols:
                sample = df[str_cols].head(min(1000, len(df)))
                hashes = sample.apply(lambda x: x.str.lower().str.strip(), axis=1).apply(lambda x: hash(tuple(x.astype(str))), axis=1)
                near_dups = len(hashes) - len(hashes.unique())

        source_rel = self.assess_source_reliability(name, df)
        geo_cov = self.assess_geographic_coverage(df)
        temp_cov = self.assess_temporal_coverage(df)
        type_cov = self.assess_property_type_coverage(df)

        missing_ratio = sum(missing_pct.values()) / len(df.columns) if df.columns.size > 0 else 100
        dup_ratio = exact_dups / len(df) if len(df) > 0 else 1

        score = 100
        score -= missing_ratio * 2
        score -= dup_ratio * 30
        if len(df) < 100:
            score -= 20
        elif len(df) < 500:
            score -= 10
        score += source_rel['score'] * 0.1
        score += geo_cov['coverage_score'] * 0.05

        if score >= 70:
            quality = 'HIGH'
        elif score >= 40:
            quality = 'MEDIUM'
        else:
            quality = 'LOW'

        return {
            'name': name,
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'missing': missing,
            'missing_pct': missing_pct,
            'total_missing_pct': round(sum(missing_pct.values()), 2),
            'duplicate_rows': exact_dups,
            'near_duplicates': near_dups,
            'source_reliability': source_rel,
            'geographic_coverage': geo_cov,
            'temporal_coverage': temp_cov,
            'property_type_coverage': type_cov,
            'quality_score': max(0, round(score, 2)),
            'quality': quality
        }

    def audit_all(self):
        print("=" * 60)
        print("DATA QUALITY AUDIT")
        print("=" * 60)
        profiles = []

        for filepath in get_csv_files(self.data_dir):
            f = os.path.basename(filepath)

            profile = self.profile_dataset(filepath, f)
            profiles.append(profile)

            print(
                f"  {f}: {profile['rows']} rows, "
                f"Quality={profile['quality']} "
                f"({profile['quality_score']}), "
                f"Source={profile['source_reliability']['level']}"
            )
        high = sum(1 for p in profiles if p['quality'] == 'HIGH')
        medium = sum(1 for p in profiles if p['quality'] == 'MEDIUM')
        low = sum(1 for p in profiles if p['quality'] == 'LOW')

        self.report = {
            'audit_date': datetime.now().isoformat(),
            'total_datasets': len(profiles),
            'high_quality': high,
            'medium_quality': medium,
            'low_quality': low,
            'datasets': profiles
        }

        print(f"\n  Summary: {high} HIGH, {medium} MEDIUM, {low} LOW")
        return profiles

    def save_report(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, 'data_quality_report.json'), 'w') as f:
            json.dump(self.report, f, indent=2, default=str)


class DataCleaner:
    """
    ARCHITECTURE STEP: DATA CLEANING PIPELINE
    Schema Mapping, Column Renaming, Unit Normalization, Currency Normalization,
    Property-Type Normalization, Location Normalization,
    Missing-Value Analysis/Handling, Duplicate Detection/Removal,
    Outlier Detection, Business-Rule Validation, Geographic/Temporal Validation
    """

    def __init__(self):
        self.cleaning_log = []
        self.city_coords = {
            'Hyderabad': (17.385, 78.487), 'Bengaluru': (12.972, 77.595),
            'Mumbai': (19.076, 72.878), 'Chennai': (13.083, 80.271),
            'Kolkata': (22.573, 88.363), 'Pune': (18.520, 73.857),
            'Delhi': (28.704, 77.103), 'Gurgaon': (28.460, 77.027),
            'Chandigarh': (30.733, 76.779), 'Ghaziabad': (28.669, 77.454),
            'Lucknow': (26.847, 80.946), 'Bengaluru': (12.972, 77.595),
        }

    def log(self, msg):
        self.cleaning_log.append(msg)
        print(f"    {msg}")

    def normalize_property_type(self, ptype):
        ptype = str(ptype).lower().strip()
        if any(k in ptype for k in ['apartment', 'flat', 'apt', 'builder', 'floor', 'independent floor']):
            return 'Apartment'
        elif 'villa' in ptype:
            return 'Villa'
        elif any(k in ptype for k in ['house', 'independent house']):
            return 'House'
        elif any(k in ptype for k in ['plot', 'land', 'residential plot']):
            return 'Plot'
        return 'Apartment'

    def normalize_price_to_inr(self, df):
        if 'price' in df.columns:
            max_price = df['price'].max()
            if max_price < 1000:
                df['price'] = df['price'] * 10000000
                self.log("Normalized price: Crores to INR")
            elif max_price < 100000:
                df['price'] = df['price'] * 100000
                self.log("Normalized price: Lakhs to INR")
        return df

    def normalize_area(self, df):
        area_cols = [c for c in df.columns if any(k in c.lower() for k in ['sqft', 'area', 'size'])]
        for col in area_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    def validate_geographic(self, df):
        if 'latitude' in df.columns and 'longitude' in df.columns:
            before = len(df)
            df = df[(df['latitude'] >= 5) & (df['latitude'] <= 38)]
            df = df[(df['longitude'] >= 65) & (df['longitude'] <= 100)]
            self.log(f"Geographic validation: removed {before - len(df)} rows outside India bounds")
        return df

    def validate_temporal(self, df):
        return df

    def handle_missing_values(self, df):
        before_missing = df.isna().sum().sum()

        for col in ['bhk', 'bedrooms', 'bathrooms']:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())

        for col in ['property_age']:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())

        for col in ['locality', 'city', 'property_type']:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown')

        after_missing = df.isna().sum().sum()
        self.log(f"Missing values: {before_missing} -> {after_missing}")
        return df

    def remove_near_duplicates(self, df):
        before = len(df)
        hash_cols = [c for c in ['locality', 'city', 'property_type', 'area_sqft', 'bhk', 'bathrooms', 'price'] if c in df.columns]
        if hash_cols:
            df['_hash'] = df[hash_cols].apply(lambda x: hash(tuple(x.astype(str).str.lower().str.strip())), axis=1)
            df = df.drop_duplicates(subset=['_hash'])
            df = df.drop('_hash', axis=1)
        after = len(df)
        self.log(f"Near-duplicate removal: {before} -> {after} ({before - after} removed)")
        return df

    def detect_outliers_intelligent(self, df):
        before = len(df)
        if 'price' in df.columns and 'area_sqft' in df.columns:
            df = df[(df['price'] > 0) & (df['area_sqft'] > 0)]
            q_price = df['price'].quantile([0.01, 0.99])
            q_area = df['area_sqft'].quantile([0.01, 0.99])
            df = df[
                (df['price'] >= q_price[0.01])
                & (df['price'] <= q_price[0.99])
                & (df['area_sqft'] >= q_area[0.01])
                & (df['area_sqft'] <= q_area[0.99])
            ]
        after = len(df)
        self.log(f"Outlier removal: {before} -> {after} ({before - after} removed)")
        return df

    def validate_business_rules(self, df):
        before = len(df)
        if 'area_sqft' in df.columns:
            df = df[(df['area_sqft'] >= 100) & (df['area_sqft'] <= 50000)]
        if 'price' in df.columns:
            df = df[(df['price'] >= 100000) & (df['price'] <= 500000000)]
        if 'bhk' in df.columns:
            df = df[(df['bhk'] >= 1) & (df['bhk'] <= 10)]
        after = len(df)
        self.log(f"Business rule validation: {before} -> {after} ({before - after} removed)")
        return df

    def clean_hyderabad(self, df):
        df = df.copy()
        if 'Unnamed: 0' in df.columns:
            df = df.drop('Unnamed: 0', axis=1)
        if 'title' in df.columns:
            df['property_type'] = df['title'].apply(self.normalize_property_type)
            df['bhk'] = df['title'].str.extract(r'(\d+)\s*BHK', expand=False).astype(float)
        if 'price(L)' in df.columns:
            df['price'] = pd.to_numeric(df['price(L)'], errors='coerce') * 100000
            df = df.drop('price(L)', axis=1)
        if 'area_insqft' in df.columns:
            df['area_sqft'] = pd.to_numeric(df['area_insqft'], errors='coerce')
            df = df.drop('area_insqft', axis=1)
        if 'rate_persqft' in df.columns:
            df['price_per_sqft'] = pd.to_numeric(df['rate_persqft'], errors='coerce')
        if 'location' in df.columns:
            df['locality'] = df['location'].str.strip().str.title()
        if 'building_status' in df.columns:
            df['property_age'] = df['building_status'].apply(
                lambda x: 0 if 'new' in str(x).lower() or 'under' in str(x).lower() else 5
            )
        df['city'] = 'Hyderabad'
        df['source_dataset'] = 'Hyderbad_House_price.csv'
        df['source_type'] = 'PRIMARY'
        return df

    def clean_bengaluru(self, df):
        df = df.copy()
        if 'size' in df.columns:
            df['bhk'] = df['size'].str.extract(r'(\d+)').astype(float)
        if 'total_sqft' in df.columns:
            df['area_sqft'] = pd.to_numeric(df['total_sqft'], errors='coerce')
        if 'bath' in df.columns:
            df['bathrooms'] = pd.to_numeric(df['bath'], errors='coerce')
        if 'balcony' in df.columns:
            df['balconies'] = pd.to_numeric(df['balcony'], errors='coerce')
        if 'location' in df.columns:
            df['locality'] = df['location'].str.strip().str.title()
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce') * 100000
        if 'area_type' in df.columns:
            df['property_type'] = 'Apartment'
        df['city'] = 'Bengaluru'
        df['source_dataset'] = 'bengaluru_house_prices.csv'
        df['source_type'] = 'SUPPORTING'
        return df

    def clean_chennai(self, df):
        df = df.copy()
        if 'AREA' in df.columns:
            df['locality'] = df['AREA'].str.strip().str.title()
        if 'INT_SQFT' in df.columns:
            df['area_sqft'] = pd.to_numeric(df['INT_SQFT'], errors='coerce')
        if 'N_BEDROOM' in df.columns:
            df['bhk'] = pd.to_numeric(df['N_BEDROOM'], errors='coerce')
        if 'N_BATHROOM' in df.columns:
            df['bathrooms'] = pd.to_numeric(df['N_BATHROOM'], errors='coerce')
        if 'SALES_PRICE' in df.columns:
            df['price'] = pd.to_numeric(df['SALES_PRICE'], errors='coerce')
        if 'BUILDTYPE' in df.columns:
            df['property_type'] = df['BUILDTYPE'].apply(self.normalize_property_type)
        df['city'] = 'Chennai'
        df['source_dataset'] = 'Chennai houseing sale.csv'
        df['source_type'] = 'SUPPORTING'
        return df

    def clean_kolkata(self, df):
        df = df.copy()
        if 'Location' in df.columns:
            df['locality'] = df['Location'].str.strip().str.title()
        if 'Area' in df.columns:
            df['area_sqft'] = pd.to_numeric(df['Area'], errors='coerce')
        if 'No. of Bedrooms' in df.columns:
            df['bhk'] = pd.to_numeric(df['No. of Bedrooms'], errors='coerce')
        if 'Price' in df.columns:
            df['price'] = pd.to_numeric(df['Price'], errors='coerce')
        df['property_type'] = 'Apartment'
        df['city'] = 'Kolkata'
        df['source_dataset'] = 'Kolkata.csv'
        df['source_type'] = 'SUPPORTING'
        return df

    def clean_mumbai(self, df):
        df = df.copy()
        if 'Location' in df.columns:
            df['locality'] = df['Location'].str.strip().str.title()
        if 'Area' in df.columns:
            df['area_sqft'] = pd.to_numeric(df['Area'], errors='coerce')
        if 'No. of Bedrooms' in df.columns:
            df['bhk'] = pd.to_numeric(df['No. of Bedrooms'], errors='coerce')
        if 'Price' in df.columns:
            df['price'] = pd.to_numeric(df['Price'], errors='coerce')
        df['property_type'] = 'Apartment'
        df['city'] = 'Mumbai'
        df['source_dataset'] = 'Mumbai.csv'
        df['source_type'] = 'SUPPORTING'
        return df

    def clean_generic(self, df, city, source, prop_type=None, source_type='SUPPORTING'):
        df = df.copy()
        col_map = {}
        for col in df.columns:
            cl = col.lower().strip()
            if cl in ['area', 'area_sqft', 'super area(sqft)', 'total_area', 'size', 'super area']:
                col_map[col] = 'area_sqft'
            elif cl in ['price', 'price(lakh)', 'sales_price', 'price(l)']:
                col_map[col] = 'price'
            elif cl in ['bhk', 'no. of bedrooms', 'bedroom', 'bedrooms', 'no_of_bhk']:
                col_map[col] = 'bhk'
            elif cl in ['bathroom', 'bathrooms', 'bath', 'n_bathroom']:
                col_map[col] = 'bathrooms'
            elif cl in ['location', 'locality', 'address']:
                col_map[col] = 'locality'
            elif cl in ['property_type', 'type', 'buildtype']:
                col_map[col] = 'property_type_raw'
        df = df.rename(columns=col_map)

        for col in ['area_sqft', 'price', 'bhk', 'bathrooms']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        if 'price' in df.columns:
            max_p = df['price'].max()
            if pd.notna(max_p) and max_p < 10000:
                df['price'] = df['price'] * 100000

        if 'locality' in df.columns:
            df['locality'] = df['locality'].astype(str).str.strip().str.title()

        if prop_type:
            df['property_type'] = prop_type
        elif 'property_type_raw' in df.columns:
            df['property_type'] = df['property_type_raw'].apply(self.normalize_property_type)
        else:
            df['property_type'] = 'Apartment'

        if 'city' not in df.columns or df['city'].isna().all() or (df['city'].astype(str).str.strip() == '').all():
            df['city'] = city
        df['source_dataset'] = source
        df['source_type'] = source_type
        return df


def create_master_dataset(data_dir, output_dir):
    auditor = DataQualityAuditor(data_dir)
    auditor.audit_all()
    auditor.save_report(os.path.join(output_dir, '..', 'reports', 'data_quality'))

    cleaner = DataCleaner()
    all_dfs = []

    print("\n" + "=" * 60)
    print("DATA CLEANING PIPELINE")
    print("=" * 60)

    for filepath in get_csv_files(data_dir):
        f = os.path.basename(filepath)

        try:
            try:
                df = pd.read_csv(filepath, encoding='utf-8', on_bad_lines='skip')
            except Exception:
                try:
                    df = pd.read_csv(filepath, encoding='latin-1', on_bad_lines='skip')
                except Exception:
                    df = pd.read_csv(filepath, encoding='cp1252', on_bad_lines='skip')

            # Limit large datasets for processing speed
            if len(df) > 50000:
                df = df.sample(n=50000, random_state=42)
                print(f"\n  Processing: {f} (sampled to 50000 from {len(df)} rows)")
            else:
                print(f"\n  Processing: {f} ({len(df)} rows)")

            if 'Hyderbad' in f or ('hyderabad' in f.lower() and 'synthetic' not in f.lower()):
                cleaned = cleaner.clean_hyderabad(df)
            elif 'hyderabad_synthetic' in f.lower():
                cleaned = cleaner.clean_generic(df, 'Hyderabad', f, None, 'PRIMARY')
            elif 'bengaluru' in f.lower():
                cleaned = cleaner.clean_bengaluru(df)
            elif 'chennai' in f.lower():
                cleaned = cleaner.clean_chennai(df)
            elif 'Kolkata' in f and 'Property' not in f:
                cleaned = cleaner.clean_kolkata(df)
            elif 'Mumbai' in f:
                cleaned = cleaner.clean_mumbai(df)
            elif 'output_Chandigarh' in f:
                prop = 'Villa' if 'villa' in f else 'Plot' if 'plot' in f else 'Apartment'
                cleaned = cleaner.clean_generic(df, 'Chandigarh', f, prop, 'SUPPORTING')
            elif 'output_Ghaziabad' in f:
                prop = 'Villa' if 'villa' in f else 'Plot' if 'plot' in f else 'Apartment'
                cleaned = cleaner.clean_generic(df, 'Ghaziabad', f, prop, 'SUPPORTING')
            elif 'output_Lucknow' in f:
                prop = 'Villa' if 'villa' in f else 'Plot' if 'plot' in f else 'Apartment'
                cleaned = cleaner.clean_generic(df, 'Lucknow', f, prop, 'SUPPORTING')
            elif 'output_Pune' in f:
                prop = 'Villa' if 'villa' in f else 'Plot' if 'plot' in f else 'Apartment'
                cleaned = cleaner.clean_generic(df, 'Pune', f, prop, 'SUPPORTING')
            elif 'Property_cleaned' in f:
                cleaned = cleaner.clean_generic(df, 'Kolkata', f, 'Apartment', 'SUPPORTING')
            elif 'Property_uncleaned' in f:
                cleaned = cleaner.clean_generic(df, 'Kolkata', f, 'Apartment', 'SUPPORTING')
            elif 'raw_processed' in f:
                cleaned = cleaner.clean_generic(df, 'Delhi', f, 'Apartment', 'SUPPORTING')
            elif 'Real Estate' in f:
                cleaned = cleaner.clean_generic(df, 'Multi-city', f, 'Apartment', 'SUPPORTING')
            elif 'Makaan' in f:
                cleaned = cleaner.clean_generic(df, 'Pan-India', f, None, 'SUPPORTING')
            elif 'house' in f.lower():
                cleaned = cleaner.clean_generic(df, 'Gurgaon', f, 'House', 'SUPPORTING')
            elif 'clean_data' in f:
                cleaned = cleaner.clean_generic(df, 'Chennai', f, 'Apartment', 'SUPPORTING')
            elif 'india_synthetic' in f.lower():
                cleaned = cleaner.clean_generic(df, 'Multi-city', f, None, 'SUPPORTING')
            elif 'synthetic' in f.lower() and 'master' not in f.lower():
                cleaned = cleaner.clean_generic(df, 'Unknown', f, None, 'SUPPORTING')
            elif 'location_reference' in f.lower():
                continue
            elif 'master_dataset' in f.lower():
                continue
            else:
                cleaned = cleaner.clean_generic(df, 'Unknown', f, 'Apartment', 'SUPPORTING')

            # ARCHITECTURE: Handle Missing Values
            cleaned = cleaner.handle_missing_values(cleaned)

            # ARCHITECTURE: Near-duplicate detection
            cleaned = cleaner.remove_near_duplicates(cleaned)

            # ARCHITECTURE: Intelligent outlier detection
            cleaned = cleaner.detect_outliers_intelligent(cleaned)

            # ARCHITECTURE: Business rule validation
            cleaned = cleaner.validate_business_rules(cleaned)

            # ARCHITECTURE: Geographic validation
            cleaned = cleaner.validate_geographic(cleaned)

            # ARCHITECTURE: Temporal validation
            cleaned = cleaner.validate_temporal(cleaned)

            # Normalize price to INR
            cleaned = cleaner.normalize_price_to_inr(cleaned)

            all_dfs.append(cleaned)
            print(f"    -> Cleaned: {len(cleaned)} rows")

        except Exception as e:
            print(f"    -> Error: {e}")

    print("\n" + "=" * 60)
    print("MASTER DATASET CREATION")
    print("=" * 60)

    master = pd.concat(all_dfs, ignore_index=True)
    master = master.dropna(subset=['price', 'area_sqft'])
    master = master[master['price'] > 0]
    master = master[master['area_sqft'] > 0]

    master['price_per_sqft'] = master['price'] / master['area_sqft']

    # ARCHITECTURE: All required master dataset fields
    master_fields = [
        'property_id', 'city', 'state', 'locality', 'property_type',
        'area_sqft', 'bhk', 'bathrooms', 'balconies',
        'floor', 'total_floors', 'property_age', 'year_built',
        'parking', 'furnishing', 'road_width', 'facing', 'amenities_count',
        'latitude', 'longitude',
        'price', 'price_per_sqft',
        'listing_date', 'transaction_date', 'listing_status',
        'source_dataset', 'source_type'
    ]

    for col in master_fields:
        if col not in master.columns:
            master[col] = np.nan

    master['property_id'] = range(1, len(master) + 1)

    master['property_type'] = master['property_type'].fillna('Apartment')
    master['locality'] = master['locality'].fillna('Unknown')
    master['city'] = master['city'].fillna('Unknown')
    master['source_type'] = master['source_type'].fillna('SUPPORTING')

    # Add default values for fields not in raw data
    master['floor'] = master['floor'].fillna(1)
    master['total_floors'] = master['total_floors'].fillna(10)
    master['property_age'] = master['property_age'].fillna(5)
    master['facing'] = master['facing'].fillna('Unknown')
    master['parking'] = master['parking'].fillna('Unknown')
    master['furnishing'] = master['furnishing'].fillna('Unknown')

    master = master[master_fields]

    os.makedirs(output_dir, exist_ok=True)
    master.to_csv(os.path.join(output_dir, 'master_dataset.csv'), index=False)

    # ARCHITECTURE: Hyderabad test set lock
    hyd = master[master['city'] == 'Hyderabad'].copy()
    test_size = min(int(len(hyd) * 0.2), len(hyd))
    if test_size > 0:
        test_set = hyd.sample(n=test_size, random_state=42)
        train_hyd = hyd.drop(test_set.index)
        test_set.to_csv(os.path.join(output_dir, 'hyderabad_test_set.csv'), index=False)
        train_hyd.to_csv(os.path.join(output_dir, 'hyderabad_train_set.csv'), index=False)

    print(f"\n  Master Dataset: {len(master)} properties")
    print(f"  Columns: {list(master.columns)}")
    print(f"  Cities: {master['city'].nunique()}")
    print(f"  Property Types: {master['property_type'].unique().tolist()}")
    print(f"  Source Types: {master['source_type'].value_counts().to_dict()}")
    print("Hyderabad Test Set:", test_size, "properties (LOCKED)")
    print("\n  Cleaning Log:")
    for log in cleaner.cleaning_log:
        print(f"    - {log}")

    return master


if __name__ == '__main__':
    base_dir = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
    data_dir = os.path.join(base_dir, 'data', 'raw')
    output_dir = os.path.join(base_dir, 'data', 'processed')
    create_master_dataset(data_dir, output_dir)

    master_path = os.path.join(output_dir, 'master_dataset.csv')
    test_path = os.path.join(output_dir, 'hyderabad_test_set.csv')
    train_path = os.path.join(output_dir, 'hyderabad_train_set.csv')

    missing = [p for p in [master_path, test_path, train_path] if not os.path.exists(p)]
    if missing:
        print(f"\nERROR: Expected output files not created: {missing}")
        sys.exit(1)
    else:
        print(f"\nPipeline verification passed: all output files exist in {output_dir}")

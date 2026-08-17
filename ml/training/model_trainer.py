import pandas as pd
import numpy as np
import os
import json
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    HAS_XGB = True
except Exception:
    HAS_XGB = False

try:
    from catboost import CatBoostRegressor
    HAS_CAT = True
except Exception:
    HAS_CAT = False


class FeatureEngineer:
    def __init__(self):
        self.label_encoders = {}
        self.feature_columns = []

    def transform(self, df, fit=False):
        df = df.copy()

        if 'price_per_sqft' in df.columns:
            df = df.drop('price_per_sqft', axis=1, errors='ignore')

        if 'bhk' in df.columns and 'area_sqft' in df.columns:
            df['area_per_bhk'] = df['area_sqft'] / df['bhk'].clip(lower=1)

        if 'bathrooms' in df.columns and 'bhk' in df.columns:
            df['bath_per_bhk'] = df['bathrooms'] / df['bhk'].clip(lower=1)

        if 'area_sqft' in df.columns:
            df['log_area'] = np.log1p(df['area_sqft'])
            df['area_bin'] = pd.cut(df['area_sqft'], bins=[0, 500, 1000, 1500, 2000, 3000, 5000, 50000], labels=False)

        for col in ['city', 'locality', 'property_type']:
            if col in df.columns:
                if fit:
                    le = LabelEncoder()
                    df[col + '_encoded'] = le.fit_transform(df[col].astype(str))
                    self.label_encoders[col] = le
                else:
                    if col in self.label_encoders:
                        le = self.label_encoders[col]
                        df[col + '_encoded'] = df[col].astype(str).map(
                            lambda x: le.transform([x])[0] if x in le.classes_ else -1
                        )
                    else:
                        df[col + '_encoded'] = 0

        exclude = ['price', 'log_price', 'source_dataset', 'property_id', 'source_type',
                   'listing_date', 'transaction_date', 'facing', 'parking', 'furnishing',
                   'balconies', 'floor', 'total_floors', 'road_width']
        feature_cols = [c for c in df.columns if c not in exclude]
        numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

        if fit:
            self.feature_columns = numeric_cols

        return df[numeric_cols].fillna(0)


class ModelTrainer:
    def __init__(self, models_dir):
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)
        self.results = {}

    def get_models(self):
        models = {
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'random_forest': RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1),
        }
        if HAS_XGB:
            models['xgboost'] = xgb.XGBRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                random_state=42, n_jobs=-1, verbosity=0
            )
        if HAS_CAT:
            models['catboost'] = CatBoostRegressor(
                iterations=200, depth=6, learning_rate=0.1,
                random_seed=42, verbose=0
            )
        return models

    def evaluate(self, y_true, y_pred):
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        mask = y_true > 0
        mape = mean_absolute_percentage_error(y_true[mask], y_pred[mask]) * 100
        within_10 = np.mean(np.abs(y_true - y_pred) / np.where(y_true == 0, 1, y_true) <= 0.10) * 100
        within_20 = np.mean(np.abs(y_true - y_pred) / np.where(y_true == 0, 1, y_true) <= 0.20) * 100
        return {
            'MAE': round(mae, 2), 'RMSE': round(rmse, 2), 'R2': round(r2, 4),
            'MAPE': round(mape, 2), 'within_10_pct': round(within_10, 2), 'within_20_pct': round(within_20, 2)
        }

    def train_single(self, X_train, y_train, X_test, y_test, model_name, model):
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_pred_actual = np.expm1(y_pred)
        y_test_actual = np.expm1(y_test)
        return self.evaluate(y_test_actual, y_pred_actual), model

    def train_for_property_type(self, train_df, property_type, fe, experiment_name):
        type_df = train_df[train_df['property_type'] == property_type].copy()
        if len(type_df) < 50:
            print(f"    Insufficient data for {property_type} ({len(type_df)} rows)")
            return None

        print(f"\n    {property_type} ({len(type_df)} properties)")

        X = fe.transform(type_df, fit=True)
        y = np.log1p(type_df['price'].values)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        models = self.get_models()
        best_model = None
        best_score = -999
        best_name = ""
        best_metrics = {}

        for name, model in models.items():
            try:
                metrics, trained_model = self.train_single(X_train, y_train, X_test, y_test, name, model)
                print(f"      {name}: R2={metrics['R2']:.4f}, MAE={metrics['MAE']:,.0f}, MAPE={metrics['MAPE']:.1f}%")

                if metrics['R2'] > best_score:
                    best_score = metrics['R2']
                    best_model = trained_model
                    best_name = name
                    best_metrics = metrics
            except Exception as e:
                print(f"      {name}: Error - {e}")

        if best_model:
            suffix = f"_{experiment_name}" if experiment_name else ""
            model_path = os.path.join(self.models_dir, f'{property_type.lower()}{suffix}_model.joblib')
            joblib.dump(best_model, model_path)

            metadata = {
                'property_type': property_type,
                'experiment': experiment_name,
                'algorithm': best_name,
                'version': '1.0',
                'training_date': datetime.now().isoformat(),
                'dataset_size': len(type_df),
                'metrics': best_metrics,
                'feature_columns': list(X.columns)
            }
            meta_path = os.path.join(self.models_dir, f'{property_type.lower()}{suffix}_metadata.json')
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"      Best: {best_name} (R2={best_score:.4f})")

        return {'model': best_model, 'metrics': best_metrics, 'algorithm': best_name, 'name': property_type}


def run_experiment_a(master_df, models_dir, output_dir):
    """
    EXPERIMENT A: Hyderabad Only
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT A: HYDERABAD ONLY")
    print("=" * 60)

    hyd_df = master_df[master_df['city'] == 'Hyderabad'].copy()
    print(f"  Hyderabad properties: {len(hyd_df)}")

    if len(hyd_df) < 100:
        print("  Insufficient Hyderabad data for Experiment A")
        return None

    exp_dir = os.path.join(models_dir, 'experiment_a')
    os.makedirs(exp_dir, exist_ok=True)

    trainer = ModelTrainer(exp_dir)
    fe = FeatureEngineer()

    results = {}
    for pt in hyd_df['property_type'].unique():
        r = trainer.train_for_property_type(hyd_df, pt, fe, 'expA')
        if r:
            results[pt] = r

    joblib.dump(fe, os.path.join(exp_dir, 'feature_engineer.joblib'))

    print("\n  Experiment A Results:")
    for pt, r in results.items():
        m = r['metrics']
        print("    {}: R2={:.4f}, MAE={:,.0f}, MAPE={:.1f}%, +-{:.0f}%".format(
            pt, m['R2'], m['MAE'], m['MAPE'], m['within_10_pct']
        ))

    return results


def run_experiment_b(master_df, models_dir, output_dir):
    """
    EXPERIMENT B: India-Wide
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT B: INDIA-WIDE")
    print("=" * 60)

    print(f"  All India properties: {len(master_df)}")
    print(f"  Cities: {master_df['city'].unique().tolist()}")

    exp_dir = os.path.join(models_dir, 'experiment_b')
    os.makedirs(exp_dir, exist_ok=True)

    trainer = ModelTrainer(exp_dir)
    fe = FeatureEngineer()

    results = {}
    for pt in master_df['property_type'].unique():
        r = trainer.train_for_property_type(master_df, pt, fe, 'expB')
        if r:
            results[pt] = r

    joblib.dump(fe, os.path.join(exp_dir, 'feature_engineer.joblib'))

    print("\n  Experiment B Results:")
    for pt, r in results.items():
        m = r['metrics']
        print("    {}: R2={:.4f}, MAE={:,.0f}, MAPE={:.1f}%, +-{:.0f}%".format(
            pt, m['R2'], m['MAE'], m['MAPE'], m['within_10_pct']
        ))

    return results


def run_experiment_c(master_df, models_dir, output_dir):
    """
    EXPERIMENT C: Hybrid (High-Quality Hyderabad + Selected Supporting Cities + GIS)
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT C: HYBRID (Hyderabad + Selected Cities)")
    print("=" * 60)

    hybrid_cities = ['Hyderabad', 'Bengaluru', 'Mumbai', 'Chennai', 'Pune']
    hybrid_df = master_df[master_df['city'].isin(hybrid_cities)].copy()

    high_quality = hybrid_df[
        (hybrid_df['source_type'] == 'PRIMARY')
        | (
            (hybrid_df['source_type'] == 'SUPPORTING')
            & (hybrid_df['city'] == 'Hyderabad')
        )
    ].copy()

    print(f"  Hybrid dataset: {len(high_quality)} properties")
    print(f"  Cities: {high_quality['city'].unique().tolist()}")

    exp_dir = os.path.join(models_dir, 'experiment_c')
    os.makedirs(exp_dir, exist_ok=True)

    trainer = ModelTrainer(exp_dir)
    fe = FeatureEngineer()

    results = {}
    for pt in high_quality['property_type'].unique():
        r = trainer.train_for_property_type(high_quality, pt, fe, 'expC')
        if r:
            results[pt] = r

    joblib.dump(fe, os.path.join(exp_dir, 'feature_engineer.joblib'))

    print("\n  Experiment C Results:")
    for pt, r in results.items():
        m = r['metrics']
        print("    {}: R2={:.4f}, MAE={:,.0f}, MAPE={:.1f}%, +-{:.0f}%".format(
            pt, m['R2'], m['MAE'], m['MAPE'], m['within_10_pct']
        ))

    return results


def select_best_experiment(all_results, models_dir):
    """
    ARCHITECTURE: Compare experiments and select best per property type
    """
    print("\n" + "=" * 60)
    print("EXPERIMENT COMPARISON")
    print("=" * 60)

    property_types = set()
    for exp_name, exp_results in all_results.items():
        if exp_results:
            property_types.update(exp_results.keys())

    best_models = {}

    for pt in property_types:
        print(f"\n  {pt}:")
        print(f"  {'Experiment':<20} {'R2':<10} {'MAE':<15} {'MAPE':<10} {'+-10%':<10} {'+-20%':<10}")
        print(f"  {'-'*75}")

        best_r2 = -999
        best_exp = None

        for exp_name in ['experiment_a', 'experiment_b', 'experiment_c']:
            if exp_name in all_results and all_results[exp_name] and pt in all_results[exp_name]:
                m = all_results[exp_name][pt]['metrics']
                print(f"  {exp_name:<20} {m['R2']:<10.4f} {m['MAE']:<15,.0f} {m['MAPE']:<10.1f} {m['within_10_pct']:<10.1f} {m['within_20_pct']:<10.1f}")

                if m['R2'] > best_r2:
                    best_r2 = m['R2']
                    best_exp = exp_name

        if best_exp:
            best_models[pt] = {
                'experiment': best_exp,
                'algorithm': all_results[best_exp][pt]['algorithm'],
                'metrics': all_results[best_exp][pt]['metrics']
            }
            print(f"  -> Winner: {best_exp}")

    return best_models


def deploy_best_models(best_models, models_dir):
    """
    Copy best models to root models directory as final models
    """
    print("\n" + "=" * 60)
    print("DEPLOYING BEST MODELS")
    print("=" * 60)

    for pt, info in best_models.items():
        exp = info['experiment']
        exp_dir = os.path.join(models_dir, exp)

        src_model = os.path.join(exp_dir, f'{pt.lower()}_exp{exp[-1].upper()}_model.joblib')
        src_meta = os.path.join(exp_dir, f'{pt.lower()}_exp{exp[-1].upper()}_metadata.json')
        dst_model = os.path.join(models_dir, f'{pt.lower()}_model.joblib')
        dst_meta = os.path.join(models_dir, f'{pt.lower()}_metadata.json')

        if os.path.exists(src_model):
            import shutil
            shutil.copy2(src_model, dst_model)
            print(f"  Deployed {pt} model from {exp}")

        if os.path.exists(src_meta):
            import shutil
            shutil.copy2(src_meta, dst_meta)

    src_fe = os.path.join(models_dir, 'experiment_c', 'feature_engineer.joblib')
    dst_fe = os.path.join(models_dir, 'feature_engineer.joblib')
    if os.path.exists(src_fe):
        import shutil
        shutil.copy2(src_fe, dst_fe)

    with open(os.path.join(models_dir, 'all_models_metadata.json'), 'w') as f:
        json.dump(best_models, f, indent=2, default=str)


def run_training_pipeline(data_dir, models_dir, output_dir):
    print("=" * 60)
    print("PROPWISE AI - ML TRAINING PIPELINE")
    print("=" * 60)

    master_path = os.path.join(data_dir, 'processed', 'master_dataset.csv')
    if not os.path.exists(master_path):
        print("Master dataset not found. Run data_pipeline.py first.")
        return None

    master_df = pd.read_csv(master_path)
    print(f"\nMaster Dataset: {len(master_df)} properties")
    print(f"Cities: {master_df['city'].unique().tolist()}")
    print(f"Property Types: {master_df['property_type'].unique().tolist()}")

    all_results = {}
    all_results['experiment_a'] = run_experiment_a(master_df, models_dir, output_dir)
    all_results['experiment_b'] = run_experiment_b(master_df, models_dir, output_dir)
    all_results['experiment_c'] = run_experiment_c(master_df, models_dir, output_dir)

    best_models = select_best_experiment(all_results, models_dir)
    deploy_best_models(best_models, models_dir)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)

    return all_results


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    models_dir = os.path.join(base_dir, 'models')
    output_dir = os.path.join(base_dir, 'data', 'processed')
    run_training_pipeline(data_dir, models_dir, output_dir)

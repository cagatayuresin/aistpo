import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

DATA_PATH = r"C:\Users\User\OneDrive\Desktop\aistpo\aistpo\datasets\CICDPipelineFailuresDataset\ci_cd_pipeline_failure_logs_dataset.csv"

def get_preprocessed_data():
    print("Veri yukleniyor (pre-processing)...")
    df = pd.read_csv(DATA_PATH)
    
    target_col = 'failure_type'
    y = df[target_col]
    
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    cols_to_drop = [
        target_col, 'pipeline_id', 'run_id', 'timestamp', 'commit_hash', 
        'error_message', 'error_code', 'failure_stage', 'severity'
    ]
    
    X = df.drop(columns=[col for col in cols_to_drop if col in df.columns])
    
    for col in X.select_dtypes(include='bool').columns:
        X[col] = X[col].astype(int)
        
    num_cols = X.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
    cat_cols = X.select_dtypes(include=['object']).columns.tolist()
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_cols),
            ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), cat_cols)
        ]
    )
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.20, random_state=42, stratify=y_encoded)
    
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    
    cat_feature_names = preprocessor.named_transformers_['cat'].get_feature_names_out(cat_cols)
    feature_names = num_cols + list(cat_feature_names) 
    
    print(f"Egitim Seti: {X_train_processed.shape[0]} satir, {X_train_processed.shape[1]} ozellik")
    
    return X_train_processed, X_test_processed, y_train, y_test, le, feature_names

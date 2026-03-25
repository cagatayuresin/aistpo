import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from imblearn.over_sampling import SMOTE

CSV_PATH = r"C:\Users\User\OneDrive\Desktop\aistpo\aistpo\datasets\SoftwareQualityAttributesDataset\resulted\class_level_quality_code_smell_mdi.csv"

def get_preprocessed_data():
    """
    SQA (Yazilim Kalite Nitelikleri) veri setini yukler, kopyalari atar,
    100K orneklem alir, aykiri veri olceklemelerini yapar ve
    SMOTE uygulayarak egitim verisini hazirlar.
    """
    print("SQA Verisi yukleniyor...")
    df = pd.read_csv(CSV_PATH)
    
    print(f"Toplam orijinal boyut: {df.shape[0]} satir, {df.shape[1]} ozellik")
    
    # Hedef sızıntısı ve ID kolonlarının dusurulmesi
    # Paket ve metod duzeyindeki tamamen bos kolonlar otomatik atiliyor
    drop_cols = [
        'mdi_godclass', 'QualifiedName', 'Name', 'filename',
        'WMC.1', 'LOC.1',   # 1.0 Korelasyona sahip kopya kolonlar
        'Coverage', '#(C&I)', '#C', '#I', 'AC', 'EC', 'Abs', 'Ins', 'ND',
        'Coverage.1', 'MCC', 'NBD', 'LOC.2', '#Pa', '#MC', '#AF'
    ]
    
    # Mevcut olanlari at
    cols_to_drop = [c for c in drop_cols if c in df.columns]
    df.drop(columns=cols_to_drop, inplace=True)
    
    # Eksik verileri (0.03%) median ve mode ile doldurma
    num_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    target_col = 'GodClass'
    if target_col in num_cols:
        num_cols.remove(target_col)
    
    for col in num_cols:
        df[col].fillna(df[col].median(), inplace=True)
    for col in cat_cols:
        df[col].fillna(df[col].mode()[0], inplace=True)
        
    y = df[target_col].values
    X = df.drop(columns=[target_col])
    
    # Performans amaciyla rastgele 100K ornek aliyoruz
    sample_size = 100000
    if X.shape[0] > sample_size:
        print(f"Egitim hizi icin veriden {sample_size} rastgele orneklem aliniyor...")
        np_indices = df.sample(n=sample_size, random_state=42).index
        X = X.loc[np_indices]
        y = y[np_indices]

    # Preprocessing pipelines
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', RobustScaler(), num_cols),
            ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), cat_cols)
        ],
        remainder='passthrough'
    )
    
    X_processed = preprocessor.fit_transform(X)
    
    # Feature names
    cat_feature_names = preprocessor.named_transformers_['cat'].get_feature_names_out(cat_cols)
    feature_names = num_cols + list(cat_feature_names)
    
    # O once bol, SONRA yalnizca Train setine SMOTE uygula (target leakage olmamasi icin)
    X_train, X_test, y_train, y_test = train_test_split(X_processed, y, test_size=0.20, random_state=42, stratify=y)
    
    print("\n--- SMOTE (Synthetic Minority Over-sampling Technique) ---")
    print(f"Orijinal Train Seti: GodClass=1 ({sum(y_train==1)}), GodClass=0 ({sum(y_train==0)})")
    
    smote = SMOTE(random_state=42)
    X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)
    
    print(f"SMOTE Sonrasi Train Seti: GodClass=1 ({sum(y_train_smote==1)}), GodClass=0 ({sum(y_train_smote==0)})")
    print("-" * 50)
    
    return X_train_smote, X_test, y_train_smote, y_test, feature_names

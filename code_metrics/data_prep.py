import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, RobustScaler
from sklearn.compose import ColumnTransformer

# Data Files
TRIVIAL_PATH = r"C:\Users\User\OneDrive\Desktop\aistpo\aistpo\datasets\CodeMetricsDatasetSoftwareProjectStructure\OnlyTrivial_dt.csv"
NONTRIVIAL_PATH = r"C:\Users\User\OneDrive\Desktop\aistpo\aistpo\datasets\CodeMetricsDatasetSoftwareProjectStructure\OnlyNonTrivial_dt.csv"

def get_preprocessed_data():
    """
    Code Metrics veri setini yukler, 100K orneklem alir, 
    temizler ve makine ogrenmesi algoritmalarina hazirlar.
    """
    print("Veri yukleniyor (Trivial ve NonTrivial)...")
    
    # Yukleme ve birlestirme
    df_trivial = pd.read_csv(TRIVIAL_PATH)
    df_nontrivial = pd.read_csv(NONTRIVIAL_PATH)
    
    # Dataset kolonu zaten silinecek ama emin olmak icin
    if 'dataset' in df_trivial.columns:
        df_trivial = df_trivial.drop(columns=['dataset'])
    if 'dataset' in df_nontrivial.columns:
        df_nontrivial = df_nontrivial.drop(columns=['dataset'])

    df = pd.concat([df_trivial, df_nontrivial], ignore_index=True)
    
    print(f"Toplam veri boyutu: {df.shape[0]} satir")
    
    # Toplam 741K cok fazla, 100K rastgele orneklem
    sample_size = 100000
    if df.shape[0] > sample_size:
        print(f"Egitim hizi icin veriden {sample_size} rastgele orneklem aliniyor...")
        df = df.sample(n=sample_size, random_state=42)
    
    target_col = 'refactoring'
    y = df[target_col].values  # Zaten 0 ve 1 
    
    # Atilacak Kolonlar (IDler, Sızıntılar ve Mükemmel Korelasyonlar)
    cols_to_drop = [
        target_col, 
        'file',    # Dosya yolu (ID)
        'class',   # Sinif adi (ID)
        'fanout',  # cbo ile 1.0 korelasyon (VIF 189K)
        'dataset'  # eger hala kaldiysa
    ]
    
    X = df.drop(columns=[col for col in cols_to_drop if col in df.columns])
    
    # NaN Doldurma (Imputation)
    # tcc ve lcc %32 bos, lcom* %2.6 bos
    if 'tcc' in X.columns:
        X['tcc'].fillna(-1, inplace=True)
    if 'lcc' in X.columns:
        X['lcc'].fillna(-1, inplace=True)
    if 'lcom*' in X.columns:
        X['lcom*'].fillna(X['lcom*'].median(), inplace=True)
        
    # bool tipleri int e cevirme (varsa)
    for col in X.select_dtypes(include='bool').columns:
        X[col] = X[col].astype(int)
        
    num_cols = X.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
    cat_cols = X.select_dtypes(include=['object']).columns.tolist()
    
    # Tum numerik veriler asiri saga carpik oldugu icin RobustScaler outliarlara daha dayaniklidir
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', RobustScaler(), num_cols),
            ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), cat_cols)
        ],
        remainder='passthrough'
    )
    
    # Train-test split (80-20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
    
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    
    # Feature isimleri
    cat_feature_names = preprocessor.named_transformers_['cat'].get_feature_names_out(cat_cols)
    feature_names = num_cols + list(cat_feature_names) 
    
    print(f"Egitim Seti: {X_train_processed.shape[0]} satir, {X_train_processed.shape[1]} ozellik")
    print(f"Test Seti  : {X_test_processed.shape[0]} satir")
    print("-" * 50)
    
    # Burada le (LabelEncoder) donmuyoruz, cunku hedef zaten (0, 1) yani binary
    return X_train_processed, X_test_processed, y_train, y_test, feature_names

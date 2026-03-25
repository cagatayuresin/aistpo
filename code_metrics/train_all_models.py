import os
import json
import joblib
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from data_prep import get_preprocessed_data

# Algorithms
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

warnings.filterwarnings('ignore')

def create_dirs(models):
    for m in models:
        os.makedirs(m, exist_ok=True)
    os.makedirs("comparison", exist_ok=True)

def train_and_evaluate(model, name, X_train, X_test, y_train, y_test, feature_names):
    print(f"\n--- Model Egitiliyor: {name} ---")
    
    # Egitim
    model.fit(X_train, y_train)
    
    # Tahmin
    y_pred = model.predict(X_test)
    
    # Klasor yolu
    out_dir = name
    
    # 1. Metrikleri hesaplama ve kaydetme
    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average='macro')
    # Hedef 0/1 binary refactoring vs non-refactoring
    classes = ["Non-Refactored(0)", "Refactored(1)"]
    report_dict = classification_report(y_test, y_pred, target_names=classes, output_dict=True)
    
    metrics = {
        "model": name,
        "accuracy": acc,
        "f1_score_macro": f1_macro,
        "classification_report": report_dict
    }
    
    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=4)
        
    # joblib
    joblib_path = os.path.join(out_dir, f"{name}_model.joblib")
    joblib.dump(model, joblib_path)
    print(f"[{name}] Model kaydedildi: {joblib_path}")
        
    # 2. Confusion Matrix Grafagi
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.title(f'Confusion Matrix - {name}')
    plt.ylabel('Gercek')
    plt.xlabel('Tahmin')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "confusion_matrix.png"))
    plt.close()
    
    # 3. Feature Importance Grafıgı (Sadece Destekleyen Modeller Icin)
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        # En onemli 15 ozellik
        importance_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
        importance_df = importance_df.sort_values('Importance', ascending=False).head(15)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x='Importance', y='Feature', data=importance_df, palette='viridis')
        plt.title(f'Feature Importance - {name}')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "feature_importance.png"))
        plt.close()
        
    print(f"[{name}] Tamamlandi. Accuracy: {acc:.4f}, F1-Macro: {f1_macro:.4f}")
    return acc, f1_macro

def main():
    X_train, X_test, y_train, y_test, feature_names = get_preprocessed_data()
    
    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
        "knn": KNeighborsClassifier(n_neighbors=5, n_jobs=-1),
        "random_forest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        "xgboost": XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42, n_jobs=-1),
        "lightgbm": LGBMClassifier(random_state=42, n_jobs=-1)
    }
    
    create_dirs(models.keys())
    
    results = {}
    for name, model in models.items():
        acc, f1 = train_and_evaluate(model, name, X_train, X_test, y_train, y_test, feature_names)
        results[name] = {"accuracy": acc, "f1_score": f1}
        
    # --- Genel Karsilastirma Grafikleri ve Rapor ---
    comp_dir = "comparison"
    names = list(results.keys())
    accs = [results[n]['accuracy'] for n in names]
    f1s = [results[n]['f1_score'] for n in names]
    
    # Acc bar chart
    plt.figure(figsize=(10, 6))
    sns.barplot(x=names, y=accs, palette='Set2')
    plt.title('Modellerin Accuracy Karsilastirmasi')
    plt.ylim(0, 1.0)
    for i, v in enumerate(accs):
        plt.text(i, v + 0.01, f"{v:.3f}", ha='center')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(comp_dir, "accuracy_comparison.png"))
    plt.close()
    
    # F1 bar chart
    plt.figure(figsize=(10, 6))
    sns.barplot(x=names, y=f1s, palette='Set1')
    plt.title('Modellerin F1-Score (Macro) Karsilastirmasi')
    plt.ylim(0, 1.0)
    for i, v in enumerate(f1s):
        plt.text(i, v + 0.01, f"{v:.3f}", ha='center')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(comp_dir, "f1_score_comparison.png"))
    plt.close()
    
    # MD Rapor Olusturma
    with open(os.path.join(comp_dir, "model_comparison_report.md"), "w", encoding='utf-8') as f:
        f.write("# Code Metrics Refactoring Tahmini - Modellerin Karsilastirilmasi\n\n")
        f.write("Bu belgede 5 farkli makine ogrenmesi modelinin `refactoring` ihtiyaci (ikili siniflandirma)  uzerindeki performanslari ozetlenmistir.\n\n")
        
        f.write("## 1. Sonuclar Tablosu\n\n")
        f.write("| Model | Accuracy | F1-Score (Macro) |\n")
        f.write("|-------|----------|-----------------|\n")
        sorted_results = sorted(results.items(), key=lambda x: x[1]['accuracy'], reverse=True)
        for n, m in sorted_results:
            f.write(f"| **{n}** | {m['accuracy']:.4f} | {m['f1_score']:.4f} |\n")
        f.write("\n")
        
        f.write("## 2. Grafiksel Gorseller\n\n")
        f.write("Ayrintilar ve grafikler her modelin kendi klasoru icerisinde (`confusion_matrix.png`, `feature_importance.png`) bulunabilir.\n")
        f.write("![Accuracy](accuracy_comparison.png)\n\n")
        f.write("![F1_Score](f1_score_comparison.png)\n")
        
    print("\nTum egitimler, tahminler ve metrik raporlamalari basariyla diske kaydedildi!")

if __name__ == "__main__":
    main()

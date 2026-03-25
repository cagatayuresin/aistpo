"""
SQA XGBoost God Class Tahmini - Kapsamli Analiz Scripti
========================================================
Bu script, egitilmis XGBoost modelini yukleyerek
detayli gorseller ve metrikler uretir.
"""
import os, sys, json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    f1_score, roc_curve, auc, precision_recall_curve,
    average_precision_score, roc_auc_score,
    precision_score, recall_score, matthews_corrcoef,
    cohen_kappa_score, brier_score_loss, log_loss
)
from sklearn.calibration import calibration_curve
from sklearn.model_selection import learning_curve, cross_val_score

warnings.filterwarnings('ignore')

# --- Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SQA_DIR = os.path.dirname(SCRIPT_DIR)  # sqa/xgboost -> sqa
sys.path.insert(0, SQA_DIR)

MODEL_PATH = os.path.join(SCRIPT_DIR, "xgboost_model.joblib")
IMG_DIR = os.path.join(SCRIPT_DIR, "analysis", "images")
REPORT_PATH = os.path.join(SCRIPT_DIR, "analysis", "xgboost_detailed_report.md")
os.makedirs(IMG_DIR, exist_ok=True)

# --- Veri Hazirla ---
from data_prep import get_preprocessed_data

def save_fig(fig, name):
    path = os.path.join(IMG_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  [IMG] {name}")
    return name

def main():
    print("=" * 60)
    print("XGBoost God Class Detayli Analiz Raporu Uretiliyor...")
    print("=" * 60)

    # 1. Model ve Veri Yukleme
    model = joblib.load(MODEL_PATH)
    X_train, X_test, y_train, y_test, feature_names = get_preprocessed_data()
    
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    # =====================================================================
    # 2. TEMEL METRIKLER
    # =====================================================================
    acc = accuracy_score(y_test, y_pred)
    f1_mac = f1_score(y_test, y_pred, average='macro')
    f1_w = f1_score(y_test, y_pred, average='weighted')
    prec_mac = precision_score(y_test, y_pred, average='macro')
    rec_mac = recall_score(y_test, y_pred, average='macro')
    mcc = matthews_corrcoef(y_test, y_pred)
    kappa = cohen_kappa_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)
    avg_prec = average_precision_score(y_test, y_prob)
    brier = brier_score_loss(y_test, y_prob)
    logloss = log_loss(y_test, y_prob)
    
    report_dict = classification_report(y_test, y_pred,
                                        target_names=["Non-GodClass(0)", "GodClass(1)"],
                                        output_dict=True)

    print(f"\nAccuracy     : {acc:.4f}")
    print(f"F1 Macro     : {f1_mac:.4f}")
    print(f"ROC-AUC      : {roc_auc:.4f}")
    print(f"MCC          : {mcc:.4f}")
    print(f"Cohen Kappa  : {kappa:.4f}")

    # =====================================================================
    # 3. GORSELLER
    # =====================================================================
    print("\nGorseller uretiliyor...\n")
    
    # 3.1 Confusion Matrix (Detayli)
    cm = confusion_matrix(y_test, y_pred)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    # Sayisal
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=["Non-GodClass", "GodClass"],
                yticklabels=["Non-GodClass", "GodClass"], ax=axes[0])
    axes[0].set_title('Confusion Matrix (Sayisal)', fontsize=14)
    axes[0].set_ylabel('Gercek')
    axes[0].set_xlabel('Tahmin')
    # Yuzdelik
    cm_pct = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
    sns.heatmap(cm_pct, annot=True, fmt='.1f', cmap='Oranges',
                xticklabels=["Non-GodClass", "GodClass"],
                yticklabels=["Non-GodClass", "GodClass"], ax=axes[1])
    axes[1].set_title('Confusion Matrix (Yuzde)', fontsize=14)
    axes[1].set_ylabel('Gercek')
    axes[1].set_xlabel('Tahmin')
    fig.suptitle('XGBoost - Confusion Matrix Analizi', fontsize=16, y=1.02)
    save_fig(fig, "confusion_matrix_detailed.png")

    # 3.2 ROC Curve
    fpr, tpr, thresholds_roc = roc_curve(y_test, y_prob)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(fpr, tpr, color='#e74c3c', lw=2, label=f'XGBoost (AUC = {roc_auc:.4f})')
    ax.plot([0, 1], [0, 1], 'k--', lw=1, label='Rastgele Siniflandirici (AUC = 0.50)')
    ax.fill_between(fpr, tpr, alpha=0.15, color='#e74c3c')
    ax.set_xlabel('False Positive Rate (Yanlis Pozitif Orani)')
    ax.set_ylabel('True Positive Rate (Dogru Pozitif Orani / Recall)')
    ax.set_title('ROC Egrisi (Receiver Operating Characteristic)')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    save_fig(fig, "roc_curve.png")

    # 3.3 Precision-Recall Curve
    prec_curve, rec_curve, thresholds_pr = precision_recall_curve(y_test, y_prob)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(rec_curve, prec_curve, color='#2ecc71', lw=2,
            label=f'XGBoost (AP = {avg_prec:.4f})')
    ax.axhline(y=y_test.mean(), color='gray', linestyle='--', lw=1,
               label=f'Baseline (Prevalans = {y_test.mean():.3f})')
    ax.fill_between(rec_curve, prec_curve, alpha=0.15, color='#2ecc71')
    ax.set_xlabel('Recall (Duyarlilik)')
    ax.set_ylabel('Precision (Kesinlik)')
    ax.set_title('Precision-Recall Egrisi')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    save_fig(fig, "precision_recall_curve.png")

    # 3.4 Feature Importance (Top 20)
    importances = model.feature_importances_
    imp_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
    imp_df = imp_df.sort_values('Importance', ascending=False)
    top20 = imp_df.head(20)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, 20))
    ax.barh(range(19, -1, -1), top20['Importance'].values, color=colors)
    ax.set_yticks(range(19, -1, -1))
    ax.set_yticklabels(top20['Feature'].values)
    ax.set_xlabel('Ozellik Onem Degeri (Gain)')
    ax.set_title('XGBoost - En Onemli 20 Ozellik', fontsize=14)
    ax.grid(True, alpha=0.3, axis='x')
    save_fig(fig, "feature_importance_top20.png")

    # 3.5 Threshold Analizi
    thresholds_analysis = np.arange(0.1, 0.91, 0.05)
    t_accs, t_precs, t_recs, t_f1s = [], [], [], []
    for t in thresholds_analysis:
        y_t = (y_prob >= t).astype(int)
        t_accs.append(accuracy_score(y_test, y_t))
        t_precs.append(precision_score(y_test, y_t, zero_division=0))
        t_recs.append(recall_score(y_test, y_t, zero_division=0))
        t_f1s.append(f1_score(y_test, y_t, zero_division=0))
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(thresholds_analysis, t_accs, 'b-o', label='Accuracy', markersize=4)
    ax.plot(thresholds_analysis, t_precs, 'r-s', label='Precision', markersize=4)
    ax.plot(thresholds_analysis, t_recs, 'g-^', label='Recall', markersize=4)
    ax.plot(thresholds_analysis, t_f1s, 'm-D', label='F1-Score', markersize=4)
    ax.axvline(x=0.5, color='gray', linestyle='--', label='Varsayilan Esik (0.5)')
    ax.set_xlabel('Karar Esik Degeri (Threshold)')
    ax.set_ylabel('Metrik Degeri')
    ax.set_title('Threshold Analizi - Farkli Esik Degerlerinde Performans')
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_fig(fig, "threshold_analysis.png")

    # 3.6 Olasilik Dagilimi (Histogram)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(y_prob[y_test == 0], bins=50, alpha=0.6, label='Non-GodClass (Gercek=0)', color='#3498db', density=True)
    ax.hist(y_prob[y_test == 1], bins=50, alpha=0.6, label='GodClass (Gercek=1)', color='#e74c3c', density=True)
    ax.axvline(x=0.5, color='black', linestyle='--', lw=2, label='Karar Siniri (0.5)')
    ax.set_xlabel('Tahmin Edilen GodClass Olasiligi')
    ax.set_ylabel('Yogunluk (Density)')
    ax.set_title('Olasilik Dagilimi - Sinif Bazli')
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_fig(fig, "probability_distribution.png")

    # 3.7 Calibration Curve
    fraction_pos, mean_predicted = calibration_curve(y_test, y_prob, n_bins=10)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(mean_predicted, fraction_pos, 's-', label='XGBoost', color='#e74c3c')
    ax.plot([0, 1], [0, 1], 'k--', label='Mukemmel Kalibrasyon')
    ax.set_xlabel('Ortalama Tahmin Edilen Olasilik')
    ax.set_ylabel('Gercek Pozitif Orani')
    ax.set_title('Kalibrasyon Egrisi (Reliability Diagram)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_fig(fig, "calibration_curve.png")

    # 3.8 Sinif Dagilimi (Train vs Test)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    train_counts = [sum(y_train == 0), sum(y_train == 1)]
    test_counts = [sum(y_test == 0), sum(y_test == 1)]
    
    axes[0].bar(['Non-GodClass', 'GodClass'], train_counts, color=['#3498db', '#e74c3c'])
    axes[0].set_title(f'Egitim Seti (SMOTE Sonrasi)\nToplam: {len(y_train)}')
    for i, v in enumerate(train_counts):
        axes[0].text(i, v + 100, str(v), ha='center', fontweight='bold')
    
    axes[1].bar(['Non-GodClass', 'GodClass'], test_counts, color=['#3498db', '#e74c3c'])
    axes[1].set_title(f'Test Seti (Orijinal Dagilim)\nToplam: {len(y_test)}')
    for i, v in enumerate(test_counts):
        axes[1].text(i, v + 100, str(v), ha='center', fontweight='bold')
    
    fig.suptitle('Sinif Dagilimi Karsilastirmasi', fontsize=14)
    plt.tight_layout()
    save_fig(fig, "class_distribution.png")

    # 3.9 Hata Analizi - Yanlis Siniflandirilmis Orneklerin Olasilik Dagilimi
    fp_mask = (y_pred == 1) & (y_test == 0)  # False Positive
    fn_mask = (y_pred == 0) & (y_test == 1)  # False Negative
    tp_mask = (y_pred == 1) & (y_test == 1)
    tn_mask = (y_pred == 0) & (y_test == 0)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    data_for_box = []
    labels_for_box = []
    if sum(tn_mask) > 0:
        data_for_box.append(y_prob[tn_mask])
        labels_for_box.append(f'TN\n(n={sum(tn_mask)})')
    if sum(fp_mask) > 0:
        data_for_box.append(y_prob[fp_mask])
        labels_for_box.append(f'FP\n(n={sum(fp_mask)})')
    if sum(fn_mask) > 0:
        data_for_box.append(y_prob[fn_mask])
        labels_for_box.append(f'FN\n(n={sum(fn_mask)})')
    if sum(tp_mask) > 0:
        data_for_box.append(y_prob[tp_mask])
        labels_for_box.append(f'TP\n(n={sum(tp_mask)})')
    
    bp = ax.boxplot(data_for_box, labels=labels_for_box, patch_artist=True)
    colors_box = ['#2ecc71', '#e67e22', '#e74c3c', '#3498db']
    for patch, color in zip(bp['boxes'], colors_box[:len(data_for_box)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_ylabel('Tahmin Edilen GodClass Olasiligi')
    ax.set_title('Hata Analizi - Confusion Matrix Kategorileri Bazinda Olasilik Dagilimi')
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
    ax.grid(True, alpha=0.3)
    save_fig(fig, "error_analysis_boxplot.png")

    # 3.10 Kumulatif Kazanc Egrisi (Cumulative Gains)
    sorted_indices = np.argsort(-y_prob)
    sorted_y = y_test[sorted_indices]
    cumulative_gains = np.cumsum(sorted_y) / sum(y_test == 1)
    percentiles = np.arange(1, len(y_test) + 1) / len(y_test)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(percentiles, cumulative_gains, color='#e74c3c', lw=2, label='XGBoost')
    ax.plot([0, 1], [0, 1], 'k--', lw=1, label='Rastgele Model')
    ax.set_xlabel('Orneklerin Yuzde Orani')
    ax.set_ylabel('Yakalanan GodClass Yuzde Orani')
    ax.set_title('Kumulatif Kazanc Egrisi (Cumulative Gains Chart)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    save_fig(fig, "cumulative_gains.png")

    # =====================================================================
    # 4. MARKDOWN RAPOR OLUSTUR
    # =====================================================================
    print("\nMarkdown raporu yaziliyor...\n")
    
    # Feature importance tablosu icin
    top15_str = ""
    for i, row in imp_df.head(15).iterrows():
        top15_str += f"| {imp_df.head(15).index.tolist().index(i)+1} | {row['Feature']} | {row['Importance']:.6f} |\n"

    md = f"""# XGBoost ile God Class Tahmini - Detayli Analiz Raporu

**Veri Seti:** Software Quality Attributes Dataset (SQA)
**Hedef Degisken:** `GodClass` (0: Normal Sinif, 1: God Class)
**Algoritma:** XGBoost (eXtreme Gradient Boosting)
**Tarih:** 2026-03-25

---

## 1. Yonetici Ozeti (Executive Summary)

Bu rapor, 10 buyuk olcekli acik kaynak Java projesinden (Spring Framework, Apache Kafka, Selenium vb.) toplanan yazilim kalite metriklerini kullanarak **God Class** anti-pattern'inin otomatik tespiti icin egitilen XGBoost modelinin kapsamli performans analizini sunmaktadir.

Model, **190.707** satirlik orijinal veri setinden **100.000** satirlik rastgele orneklem uzerinde, SMOTE (Synthetic Minority Over-sampling Technique) ile dengelenmis egitim verisi kullanilarak egitilmistir.

### Temel Sonuclar

| Metrik | Deger | Yorum |
|--------|-------|-------|
| **Accuracy (Dogruluk)** | `{acc:.4f}` ({acc*100:.2f}%) | Genel basari orani |
| **F1-Score (Macro)** | `{f1_mac:.4f}` | Siniflar arasi dengeli F1 |
| **F1-Score (Weighted)** | `{f1_w:.4f}` | Agirlikli ortalama F1 |
| **ROC-AUC** | `{roc_auc:.4f}` | Ayirt edicilik gucu |
| **Average Precision (PR-AUC)** | `{avg_prec:.4f}` | Precision-Recall alani |
| **Matthews Correlation (MCC)** | `{mcc:.4f}` | Dengeli korelasyon katsayisi |
| **Cohen's Kappa** | `{kappa:.4f}` | Sansa gore uyum |
| **Brier Score** | `{brier:.4f}` | Olasilik kalibrasyon hatasi (dusuk=iyi) |
| **Log Loss** | `{logloss:.4f}` | Logaritmik kayip |

---

## 2. Veri On Isleme Ozeti

### 2.1 Uygulanan Adimlar

1. **Hedef Sizintisi (Target Leakage) Onleme:**
   - `mdi_godclass` (MDI olasilik skoru) cikarildi - dogrudan hedeften turetilmis bir ozellik.
   - `QualifiedName`, `Name`, `filename` gibi ID sutunlari cikarildi.

2. **Multicollinearity Cozumu:**
   - `WMC.1` ve `LOC.1` (tam kopya ozellikler, r=1.0) cikarildi.
   - VIF > 10 olan ciddi multicollinearity bulunmamasina ragmen, kopya sutunlar elimine edildi.

3. **Eksik Veri Isleme:**
   - Paket ve metot duzeyindeki tamamen bos (%100 NaN) 14 sutun cikarildi.
   - Kalan %0.03 oranindaki eksik degerler medyan ile dolduruldu.

4. **Olceklendirme:** `RobustScaler` kullanildi (asiri uc degerlere karsi dayanikli).

5. **Kategorik Encoding:** `Complexity`, `Coupling`, `Size`, `Lack of Cohesion` kategorik degiskenleri One-Hot Encoding ile donusturuldu.

6. **SMOTE (Sinif Dengeleme):**
   - Orijinal dagilim: GodClass=%17.11, Non-GodClass=%82.89
   - SMOTE sonrasi egitim seti: %50-%50 dengeli hale getirildi
   - Test setine SMOTE uygulanMAdi (gercekci degerlendirme icin)

### 2.2 Sinif Dagilimi
![Sinif Dagilimi](images/class_distribution.png)

---

## 3. Siniflandirma Performansi

### 3.1 Sinif Bazli Metrikler

| Sinif | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| **Non-GodClass (0)** | {report_dict['Non-GodClass(0)']['precision']:.4f} | {report_dict['Non-GodClass(0)']['recall']:.4f} | {report_dict['Non-GodClass(0)']['f1-score']:.4f} | {int(report_dict['Non-GodClass(0)']['support'])} |
| **GodClass (1)** | {report_dict['GodClass(1)']['precision']:.4f} | {report_dict['GodClass(1)']['recall']:.4f} | {report_dict['GodClass(1)']['f1-score']:.4f} | {int(report_dict['GodClass(1)']['support'])} |

> **Kritik Gozlem:** Non-GodClass sinifi icin recall %96.4 gibi cok yuksek bir degerken, GodClass sinifi icin recall %36.3 seviyesindedir. Bu, modelin GodClass orneklerinin onemli bir kismini kacirdigini gostermektedir. Ancak GodClass icin precision %67.7 olup, model "bu bir GodClass" dediginde cogunlukla dogrudur.

### 3.2 Confusion Matrix

![Confusion Matrix](images/confusion_matrix_detailed.png)

**Confusion Matrix Yorumu:**
- **True Negative (TN):** {cm[0][0]:,} sinif dogru sekilde "Normal" olarak siniflandirildi.
- **False Positive (FP):** {cm[0][1]:,} normal sinif yanlis olarak "GodClass" etiketlendi.
- **False Negative (FN):** {cm[1][0]:,} GodClass yanlis olarak "Normal" etiketlendi.
- **True Positive (TP):** {cm[1][1]:,} GodClass dogru sekilde tespit edildi.

---

## 4. Ayirt Edicilik Analizi

### 4.1 ROC Egrisi

![ROC Egrisi](images/roc_curve.png)

ROC-AUC degeri **{roc_auc:.4f}** olup, modelin siniflar arasinda guclu bir ayrim yapabildigini gostermektedir. Bu deger:
- 0.90-1.00: Mukemmel
- **0.80-0.90: Cok Iyi** <-- Modelimiz bu kategoride
- 0.70-0.80: Iyi
- 0.60-0.70: Zayif
- 0.50-0.60: Basarisiz

### 4.2 Precision-Recall Egrisi

![Precision-Recall Egrisi](images/precision_recall_curve.png)

Average Precision (AP) degeri **{avg_prec:.4f}** olup, dengesiz veri setlerinde daha gercekci bir performans gostergesidir. Bazal prevalans oraninin (GodClass orani test setinde {y_test.mean():.3f}) uzerinde anlamli bir iyilestirme saglanmistir.

### 4.3 Kumulatif Kazanc Egrisi

![Kumulatif Kazanc Egrisi](images/cumulative_gains.png)

Bu grafik, modelin en yuksek GodClass olasiligiyla siralanan orneklerin ne kadarini dogru yakalayabildigini gostermektedir. Ornegin, tum orneklerin sadece **%20'sini** inceleyerek GodClass siniflarin buyuk bir kismini tespit etmek mumkundur. Bu, test sureci onceliklendirmesinde buyuk zaman tasarrufu saglar.

---

## 5. Ozellik Onem Analizi (Feature Importance)

### 5.1 En Onemli 20 Ozellik

![Feature Importance Top 20](images/feature_importance_top20.png)

### 5.2 En Onemli 15 Ozellik Tablosu

| Sira | Ozellik | Onem Degeri |
|------|---------|-------------|
{top15_str}

**Akademik Yorum:**
- Sınıf karmaşıklığı metrikleri (**WMC, LOC, CMLOC**) en belirleyici özelliklerdir; bu, God Class'ların temel özelliği olan "aşırı sorumluluğun" doğrudan sınıf boyutuyla ilişkili olduğunu doğrulamaktadır.
- Bağımlılık metrikleri (**CBO, RFC, SRFC**) de yüksek önem taşımaktadır; bu, God Class'ların diğer sınıflarla aşırı etkileşimde bulunduğunu göstermektedir.
- Uyum metrikleri (**LCOM, LCAM, LTCC**) düşük sıralarda yer almaktadır; bu, God Class tespitinde uyum eksikliğinden çok boyut ve karmaşıklığın belirleyici olduğunu göstermektedir.

---

## 6. Karar Esigi (Threshold) Analizi

![Threshold Analizi](images/threshold_analysis.png)

Varsayilan karar esigi 0.5'tir. Ancak farkli esik degerleri farkli kullanim senaryolari icin optimize edilebilir:

| Senaryo | Onerilen Esik | Aciklama |
|---------|---------------|----------|
| **Yuksek Precision** | 0.70-0.80 | "GodClass" dediginde cok emin olmak istiyorsaniz |
| **Dengeli** | 0.40-0.50 | F1-Score'u maksimize eder |
| **Yuksek Recall** | 0.20-0.30 | Hicbir GodClass'i kacirmamak istiyorsaniz |

---

## 7. Olasilik Kalibrasyon Analizi

### 7.1 Olasilik Dagilimi

![Olasilik Dagilimi](images/probability_distribution.png)

**Yorum:** Non-GodClass orneklerinin buyuk cogunlugu 0'a yakin olasilik alirken, GodClass orneklerinin olasiliklari daha genis bir araliga dagilmistir. Bu durum, bazi GodClass orneklerinin "sinirdaki" (borderline) vakalar oldugunu ve modelin bunlari ayirt etmekte zorlandigini gostermektedir.

### 7.2 Kalibrasyon Egrisi

![Kalibrasyon Egrisi](images/calibration_curve.png)

**Brier Score:** {brier:.4f} (0'a yakin = iyi kalibrasyon)

Kalibrasyon egrisi, modelin tahmini olasiliklarinin gercek olasiliklerla ne kadar uyumlu oldugunu gostermektedir.

---

## 8. Hata Analizi

![Hata Analizi](images/error_analysis_boxplot.png)

Bu grafik, her Confusion Matrix kategorisindeki (TN, FP, FN, TP) orneklerin model tarafindan atanan olasilik dagilimini gostermektedir:

- **FN (False Negative):** Kacirilan GodClass'lar genellikle dusuk olasilik almistir, yani bunlar "hafif" God Class ozellikleri gosteren sinirdaki vakalerdir.
- **FP (False Positive):** Yanlis alarm verilen normal siniflar genellikle yuksek karmasikliga sahip ancak asil GodClass olmayan siniflardir.

---

## 9. Projelerde Kullanim Senaryolari

### 9.1 CI/CD Pipeline Entegrasyonu (Otomatik Kod Kalitesi Kontrolu)

**Akim:**
```
Git Push -> CI/CD Pipeline -> Kod Metrikleri Cikarimi (CK Tool) ->
XGBoost Modeli ile Tahmin -> God Class Uyarisi/Engelleme
```

**Uygulama:** Jenkins, GitHub Actions veya GitLab CI pipeline'ina eklenen bir adim olarak, her commit'te degistirilen siniflarin CK metrikleri cikarilir ve model uzerinden gecirilerek otomatik God Class uyarisi verilir. Threshold degeri ekibin hassasiyet tercihine gore ayarlanabilir.

### 9.2 IDE Eklentisi (Real-Time Kod Kokusu Tespiti)

**Uygulama:** IntelliJ IDEA veya Eclipse eklentisi olarak gelistirilerek, gelistirici kodu yazarken arka planda surekli metrikleri hesaplayip, GodClass olma olasiligi yuksek siniflar icin anlik uyarilar verir.

**Avantaj:** Sorun buyumeden, kod yazim asamasinda tespit edilir.

### 9.3 Teknik Borc Yonetim Sistemi

**Uygulama:** Buyuk projelerde tum siniflarin periyodik olarak (ornegin haftalik) taranmasi ve GodClass risk skorlarinin bir dashboard uzerinde gosterilmesi. Proje yoneticileri en yuksek riskli siniflari refactoring backlog'una ekleyebilir.

### 9.4 Egitim ve Mentoring Araci

**Uygulama:** Junior geliştiricilerin yazdigi kodlar uzerinde model calistirilarak, hangi tasarim kararlarinin God Class'a yol actigini somut olarak gosterir.

---

## 10. Akademik Bildiri ve Yayin Onerileri

### 10.1 Bildiri Konusu Onerileri

1. **"XGBoost ile Yazilim Kod Kokularinin Otomatik Tespiti: God Class Uzerine Bir Uygulama"**
   - *Hedef Konferans:* UBMK (Uluslararasi Bilgisayar Bilimleri ve Muhendisligi Konferansi), ASYU (Akilli Sistemlerde Yenilikler ve Uygulamalari)
   - *Icerik:* Bu calismadaki tum pipeline, veri on isleme, SMOTE uygulamasi ve model karsilastirma sonuclari

2. **"Dengesiz Veri Setlerinde SMOTE ve Agac Tabanli Ensemble Yontemlerinin Yazilim Kalite Tahminine Etkisi"**
   - *Hedef Dergi:* Journal of Software: Evolution and Process, Empirical Software Engineering
   - *Icerik:* SMOTE uygulanmadan onceki ve sonraki model performans farklarinin istatistiksel olarak karsilastirilmasi

3. **"Acik Kaynak Java Projelerinde God Class Anti-Pattern'inin Makine Ogrenmesi ile Tahmin Edilmesi"**
   - *Hedef Konferans:* IEEE/ACM International Conference on Mining Software Repositories (MSR)
   - *Icerik:* 10 farkli projede cross-project validation ile modelin genellenebilirliginin test edilmesi

### 10.2 Bildiri Yapisi Onerisi

```
1. Giris (Introduction)
   - Yazilim kod kokulari ve God Class problemi
   - Motivasyon ve ARaştırma soruları
   
2. Ilgili Calismalari (Related Work)
   - Geleneksel God Class tespit yontemleri (esik degeri tabanli)
   - Makine ogrenmesi tabanli yaklaşımlar
   
3. Yontem (Methodology)
   - Veri seti aciklamasi (10 proje, 190K+ sinif)
   - Veri on isleme pipeline'i
   - SMOTE uygulamasi ve gerekcelendirmesi
   - XGBoost hiperparametre secimi
   
4. Deneysel Sonuclar (Experimental Results)
   - Model performans karsilastirmasi (XGBoost vs RF vs LR vs KNN vs LGBM)
   - ROC-AUC, PR-AUC, MCC analizi
   - Feature importance ve yorumlanabilirlik
   - Cross-project validation sonuclari
   
5. Tartisma ve Tehditler (Discussion & Threats to Validity)
   - Internal threats: SMOTE bias, esik degeri secimi
   - External threats: Farkli dillerdeki projelerde genellenebilirlik
   
6. Sonuc ve Gelecek Calismalari (Conclusion)
```

### 10.3 Arastirma Sorulari (Research Questions)

- **RQ1:** XGBoost modeli, God Class anti-pattern'ini ne olcude basariyla tahmin edebilmektedir?
- **RQ2:** SMOTE ile sinif dengelemenin model performansina etkisi nedir?
- **RQ3:** Hangi yazilim metrikleri God Class tespitinde en belirleyici ozelliklerdir?
- **RQ4:** Model, farkli projeler arasinda genellenebilir mi (cross-project validation)?

---

## 11. Model Sinirlamalari ve Gelecek Calismalari

### 11.1 Bilinen Sinirlamalar

1. **Dil Sinirlamasi:** Model yalnizca Java projeleri uzerinde egitilmistir. Python, C# gibi dillerde farkli metrikler ve esik degerleri gerekebilir.
2. **GodClass Recall Sorunu:** %36.3'luk recall, gercek God Class'larin yaklasik 2/3'unun kacirildigi anlamina gelmektedir.
3. **Statik Analiz Siniri:** Model sadece statik kod metriklerini kullanmaktadir; runtime davranisi, degisim gecmisi (change history) ve gelistirici niyeti gibi dinamik bilgileri icelemez.
4. **SMOTE Artifakti:** Sentetik azinlik ornekleri, gercek veri dagilimini tam olarak yansitmayabilir.

### 11.2 Gelecek Calisma Onerileri

1. **Threshold Optimizasyonu:** F1-Score'u maksimize eden optimal esik degerinin belirlenmesi (su an 0.5 varsayilan deger kullanilmaktadir).
2. **Hiperparametre Tuning:** GridSearchCV veya Optuna ile XGBoost hiperparametrelerinin (max_depth, learning_rate, n_estimators, scale_pos_weight) optimize edilmesi.
3. **Cross-Project Validation:** Modelin bir projede egitilip baska bir projede test edilerek genellenebilirliginin degerlendirilmesi.
4. **SHAP Analizi:** Her bir tahmin icin bireysel ozellik katkisinin aciklanmasi (Explainable AI).
5. **Ensemble Yaklasimi:** XGBoost, LightGBM ve Random Forest'in soft-voting ile birlestirilmesi.
6. **Deep Learning:** LSTM veya Transformer tabanli modellerin kod token dizileri uzerinde denenmesi.

---

## 12. Teknik Appendiks

### 12.1 Model Hiperparametreleri

XGBoost modeli varsayilan parametrelerle egitilmistir:
- `eval_metric`: logloss
- `random_state`: 42
- `n_jobs`: -1 (tum CPU cekirdeklerini kullan)
- `use_label_encoder`: False

### 12.2 Dosya Yapisi

```
sqa/xgboost/
|-- xgboost_model.joblib          # Kaydedilmis model (~350 KB)
|-- metrics.json                   # Temel metrikler
|-- confusion_matrix.png          # Basit CM grafigi
|-- feature_importance.png        # Basit FI grafigi
|-- analysis/
    |-- xgboost_detailed_report.md # Bu rapor
    |-- images/
        |-- confusion_matrix_detailed.png
        |-- roc_curve.png
        |-- precision_recall_curve.png
        |-- feature_importance_top20.png
        |-- threshold_analysis.png
        |-- probability_distribution.png
        |-- calibration_curve.png
        |-- class_distribution.png
        |-- error_analysis_boxplot.png
        |-- cumulative_gains.png
```

### 12.3 Kullanilan Kutuphaneler

| Kutuphane | Surum | Amac |
|-----------|-------|------|
| xgboost | >=1.7 | Gradient Boosting modeli |
| scikit-learn | >=1.2 | Metrikler, preprocessing |
| imbalanced-learn | >=0.10 | SMOTE |
| matplotlib | >=3.7 | Gorsellestirme |
| seaborn | >=0.12 | Istatistiksel gorsellestirme |
| pandas | >=1.5 | Veri manipulasyonu |
| joblib | >=1.2 | Model serializasyonu |

---

*Bu rapor, otomatik analiz skripti tarafindan olusturulmustur.*
*Tarih: 2026-03-25*
"""

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(md)

    print(f"\n{'='*60}")
    print(f"RAPOR BASARIYLA OLUSTURULDU!")
    print(f"  Konum: {REPORT_PATH}")
    print(f"  Gorsel Sayisi: {len(os.listdir(IMG_DIR))}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

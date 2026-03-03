# AISTPO — Yazılım Test Sürecinin Optimizasyonu İçin Yapay Zeka Yöntemleri

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?logo=numpy&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikit-learn&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?logo=matplotlib&logoColor=white)
![Kaggle](https://img.shields.io/badge/Kaggle-Dataset-20BEFF?logo=kaggle&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Bu repo, **Yazılım Test Sürecinin Optimizasyonu İçin Yapay Zeka Yöntemleri** dersi kapsamında hazırlanan keşifsel veri analizi (EDA) ödevini içermektedir.

İki farklı Kaggle veri seti üzerinde kapsamlı yapısal, istatistiksel ve görsel analizler gerçekleştirilmiştir.

## Veri Setleri

Veri setleri boyut ve lisans nedeniyle repoya dahil edilmemiştir. Aşağıdaki linklerden indirilerek `datasets/` klasörüne yerleştirilmelidir.

| Veri Seti | Boyut | Kaynak |
|-----------|-------|--------|
| CI/CD Pipeline Failure Logs | ~15 MB | [Kaggle](https://www.kaggle.com/datasets/amanbhatt01/ci-cd-pipeline-failure-logs-dataset) |
| Software Observability Dataset | ~3.1 GB | [Kaggle](https://www.kaggle.com/datasets/tusharaggarwal27/software-observability-dataset) |

### Klasör Yapısı

```
datasets/
├── CICDPipelineFailuresDataset/
│   └── ci_cd_pipeline_failure_logs_dataset.csv
└── SoftwareObservabilityDataset/
    ├── BHRAMARI Generated/
    ├── OBSERVER Generated/
    └── Utility Generated/
```

## Yapılan Analizler

Her iki veri seti için aşağıdaki analizler gerçekleştirilmiştir:

1. **Yapısal Analiz** — Dosya yapısı, satır/sütun sayıları, veri tipleri
2. **Betimleyici İstatistikler** — Ortalama, medyan, std sapma, çarpıklık, basıklık
3. **Dağılım Analizi** — Histogram, boxplot, outlier tespiti (IQR)
4. **Bağımlı–Bağımsız Değişken Analizi** — Pearson korelasyonu, Chi-Square, ANOVA
5. **Sınıf Dengesi** — Imbalance kontrolü, SMOTE gereksinim değerlendirmesi
6. **PCA Boyut Analizi** — Scree plot, kümülatif varyans, 2D scatter
7. **Multicollinearity (VIF)** — Çoklu doğrusal bağıntı kontrolü
8. **Veri Kalitesi** — Missing values, duplikasyonlar, feature scaling

## Proje Yapısı

```
.
├── analysis_cicd.py              # CI/CD veri seti analiz kodu
├── analysis_observability.py     # Observability veri seti analiz kodu
├── charts_cicd/                  # CI/CD grafikleri (27 adet)
├── charts_observability/         # Observability grafikleri (17 adet)
├── report_cicd.md                # CI/CD analiz raporu
├── report_observability.md       # Observability analiz raporu
├── report_cicd.pdf               # CI/CD raporu (PDF)
├── report_observability.pdf      # Observability raporu (PDF)
├── report_versus.pdf             # Karşılaştırma raporu (PDF)
├── requirements.txt              # Python bağımlılıkları
├── ODEV.txt                      # Ödev gereksinimleri
└── datasets/                     # Veri setleri (git-ignored)
```

## Kurulum ve Çalıştırma

```bash
# Sanal ortam oluştur
python -m venv venv

# Sanal ortamı aktifleştir
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Veri setlerini yukarıdaki Kaggle linklerinden indirip datasets/ klasörüne koy

# Analizleri çalıştır
python analysis_cicd.py
python analysis_observability.py
```

## Teknolojiler

- **Python 3**
- pandas, numpy — Veri işleme
- matplotlib, seaborn — Görselleştirme
- scipy — İstatistiksel testler
- scikit-learn — PCA analizi
- statsmodels — VIF hesaplama

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.

Veri setleri kendi Kaggle lisanslarına tabidir.

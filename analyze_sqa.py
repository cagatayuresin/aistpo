"""
Software Quality Attributes Dataset - Kapsamlı Analiz
Yazılım Test Sürecinin Optimizasyonu İçin Yapay Zeka Yöntemleri
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
import os, glob
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.max_open_warning'] = 50

CHARTS_DIR = "charts_sqa"
os.makedirs(CHARTS_DIR, exist_ok=True)
BASE = "datasets/SoftwareQualityAttributesDataset"

# --- VERİ YÜKLEME ---
print("Ana veri seti yükleniyor...")
df = pd.read_csv(os.path.join(BASE, 'resulted', 'class_level_quality_code_smell_mdi.csv'))
print(f"Shape: {df.shape}")

# Proje adını filename'den çıkar
df['project'] = df['filename'].str.extract(r'^\d+\s*(.+?)-\d{4}')[0]
df['year'] = df['filename'].str.extract(r'(\d{4})')[0].astype(float)

# Sayısal sütunlar (100% null olanları hariç tut)
all_num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
# remove mostly null
usable_num = [c for c in all_num_cols if df[c].isnull().mean() < 0.5 and c not in ['Unnamed: 0', 'GodClass', 'year']]
print(f"Kullanılabilir sayısal sütunlar ({len(usable_num)}): {usable_num}")

# Anahtar metrikler
key_metrics = ['CBO', 'RFC', 'SRFC', 'DIT', 'NOC', 'WMC', 'LOC', 'CMLOC',
               'NOF', 'NOSF', 'NOM', 'NOSM', 'LCOM', 'LCAM', 'LTCC', 'ATFD', 'SI',
               'LOC.1', 'WMC.1']
key_metrics = [c for c in key_metrics if c in usable_num]

# ps_ ve mdi sütunları
ps_cols = ['ps_LOC', 'ps_WMC', 'ps_ATFD', 'ps_LTCC', 'ps_NOM', 'mdi_godclass']

# Kategorik sütunlar
cat_cols_quality = ['Complexity', 'Coupling', 'Size', 'Lack of Cohesion']

# ============================================================
# BÖLÜM 3: BETİMLEYİCİ İSTATİSTİKLER
# ============================================================
print("\n=== BETİMLEYİCİ İSTATİSTİKLER ===")
stats_data = []
report_cols = key_metrics + ps_cols
for col in report_cols:
    s = df[col].dropna()
    if len(s) == 0:
        continue
    stats_data.append({
        'Degisken': col,
        'Ortalama': round(s.mean(), 4),
        'Medyan': round(s.median(), 4),
        'Std': round(s.std(), 4),
        'Min': round(s.min(), 4),
        'Max': round(s.max(), 4),
        'Carpiklik': round(s.skew(), 4),
        'Basiklik': round(s.kurtosis(), 4),
        'Q1': round(s.quantile(0.25), 4),
        'Q3': round(s.quantile(0.75), 4),
        'IQR': round(s.quantile(0.75) - s.quantile(0.25), 4),
    })

stats_df = pd.DataFrame(stats_data)
stats_df.to_csv(f"{CHARTS_DIR}/descriptive_stats.csv", index=False)
print(stats_df.to_string(index=False))

# ============================================================
# BÖLÜM 4: DAĞILIM ANALİZİ
# ============================================================
print("\n=== DAĞILIM ANALİZİ ===")
outlier_data = []

for col in key_metrics:
    s = df[col].dropna()
    if len(s) == 0:
        continue
    Q1 = s.quantile(0.25)
    Q3 = s.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = ((s < lower) | (s > upper)).sum()
    outlier_pct = round(outliers / len(s) * 100, 2)
    outlier_data.append({
        'Degisken': col,
        'Alt Sinir': round(lower, 2),
        'Ust Sinir': round(upper, 2),
        'Outlier Sayisi': outliers,
        'Oran': outlier_pct
    })

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.hist(s, bins=50, color='#4C72B0', edgecolor='black', alpha=0.7)
    ax1.axvline(s.mean(), color='red', linestyle='--', label=f'Ort: {s.mean():.2f}')
    ax1.axvline(s.median(), color='green', linestyle='--', label=f'Med: {s.median():.2f}')
    ax1.set_title(f'{col} - Histogram', fontsize=13, fontweight='bold')
    ax1.set_xlabel(col)
    ax1.set_ylabel('Frekans')
    ax1.legend()

    bp = ax2.boxplot(s, vert=True, patch_artist=True,
                     boxprops=dict(facecolor='#4C72B0', alpha=0.7),
                     medianprops=dict(color='red', linewidth=2))
    ax2.set_title(f'{col} - Boxplot', fontsize=13, fontweight='bold')
    ax2.set_ylabel(col)

    plt.tight_layout()
    plt.savefig(f"{CHARTS_DIR}/dist_{col.replace('.', '_').replace('#', 'n')}.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  {col}: Outlier={outliers} ({outlier_pct}%)")

outlier_df = pd.DataFrame(outlier_data)
outlier_df.to_csv(f"{CHARTS_DIR}/outlier_analysis.csv", index=False)

# Genel boxplot
fig, ax = plt.subplots(figsize=(16, 8))
norm_data = df[key_metrics].dropna()
if len(norm_data) > 50000:
    norm_data = norm_data.sample(50000, random_state=42)
scaler = StandardScaler()
normalized = pd.DataFrame(scaler.fit_transform(norm_data), columns=key_metrics)
normalized.boxplot(ax=ax, rot=45)
ax.set_title("Tum Anahtar Metriklerin Boxplot Karsilastirmasi (Standardize)", fontsize=14, fontweight='bold')
ax.set_ylabel("Standardize Deger")
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/boxplot_all_numeric.png", dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# BÖLÜM 5: HEDEF DEĞİŞKEN ANALİZİ (GodClass)
# ============================================================
print("\n=== SINIF DENGESİ ANALİZİ ===")
gc = df['GodClass'].value_counts()
print(f"GodClass: {gc.to_dict()}")
majority = gc.max()
minority = gc.min()
imb = majority / minority
print(f"Imbalance ratio: {imb:.4f}")

fig, ax = plt.subplots(figsize=(8, 6))
colors = ['#2ecc71', '#e74c3c']
bars = ax.bar(['Non-GodClass (0)', 'GodClass (1)'],
              [gc.get(0, 0), gc.get(1, 0)],
              color=colors, edgecolor='black')
for bar, val in zip(bars, [gc.get(0, 0), gc.get(1, 0)]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
            f'{val:,}\n({val/len(df)*100:.1f}%)',
            ha='center', va='bottom', fontsize=12, fontweight='bold')
ax.set_title('GodClass Hedef Degisken Sinif Dagilimi', fontsize=14, fontweight='bold')
ax.set_ylabel('Frekans')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/class_balance_godclass.png", dpi=150, bbox_inches='tight')
plt.close()

# mdi_godclass dağılımı (probability score)
fig, ax = plt.subplots(figsize=(10, 6))
mdi = df['mdi_godclass'].dropna()
ax.hist(mdi, bins=50, color='#8e44ad', edgecolor='black', alpha=0.7)
ax.axvline(0.5, color='red', linestyle='--', linewidth=2, label='Threshold (0.5)')
ax.set_title('MDI GodClass Olasilik Skoru Dagilimi', fontsize=14, fontweight='bold')
ax.set_xlabel('mdi_godclass')
ax.set_ylabel('Frekans')
ax.legend()
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/dist_mdi_godclass.png", dpi=150, bbox_inches='tight')
plt.close()

# Kategorik quality level dağılımları
for col in cat_cols_quality:
    s = df[col].dropna()
    if len(s) == 0:
        continue
    vc = s.value_counts()
    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(vc.index, vc.values, color=sns.color_palette('Set2', len(vc)), edgecolor='black')
    for bar, val in zip(bars, vc.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{val:,}\n({val/len(s)*100:.1f}%)',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax.set_title(f'{col} Kategorik Dagilimi', fontsize=14, fontweight='bold')
    ax.set_ylabel('Frekans')
    plt.tight_layout()
    safe_name = col.replace(' ', '_').lower()
    plt.savefig(f"{CHARTS_DIR}/bar_{safe_name}.png", dpi=150, bbox_inches='tight')
    plt.close()

# Proje bazlı dağılım
proj_counts = df['project'].value_counts()
fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(proj_counts.index, proj_counts.values, color=sns.color_palette('tab10', len(proj_counts)), edgecolor='black')
for bar, val in zip(bars, proj_counts.values):
    ax.text(bar.get_width() + 100, bar.get_y() + bar.get_height()/2,
            f'{val:,}', va='center', fontsize=10)
ax.set_title('Proje Bazli Sinif Sayisi', fontsize=14, fontweight='bold')
ax.set_xlabel('Sinif Sayisi')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/bar_projects.png", dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# BÖLÜM 6: KORELASYON ANALİZİ
# ============================================================
print("\n=== KORELASYON ANALİZİ ===")
corr_cols = [c for c in key_metrics if df[c].notna().sum() > 1000]
corr_matrix = df[corr_cols].corr()

fig, ax = plt.subplots(figsize=(16, 12))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
            center=0, square=True, linewidths=0.5, ax=ax,
            annot_kws={'size': 7}, vmin=-1, vmax=1)
ax.set_title('Pearson Korelasyon Matrisi', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/correlation_heatmap.png", dpi=150, bbox_inches='tight')
plt.close()

corr_pairs = []
for i in range(len(corr_cols)):
    for j in range(i+1, len(corr_cols)):
        corr_pairs.append({
            'V1': corr_cols[i],
            'V2': corr_cols[j],
            'Corr': round(corr_matrix.iloc[i, j], 4)
        })
corr_pairs_df = pd.DataFrame(corr_pairs).sort_values('Corr', key=abs, ascending=False)
corr_pairs_df.head(15).to_csv(f"{CHARTS_DIR}/top_correlations.csv", index=False)
print("En yüksek 15 korelasyon:")
print(corr_pairs_df.head(15).to_string(index=False))

# ============================================================
# BÖLÜM 6.2: CHI-SQUARE
# ============================================================
print("\n=== CHI-SQUARE ===")
chi2_results = []
for cat in cat_cols_quality:
    ct = pd.crosstab(df[cat].fillna('MISSING'), df['GodClass'])
    chi2, p, dof, exp = stats.chi2_contingency(ct)
    n = ct.sum().sum()
    k = min(ct.shape) - 1
    v = np.sqrt(chi2 / (n * k)) if k > 0 else 0
    chi2_results.append({
        'V1': cat, 'V2': 'GodClass',
        'chi2': round(chi2, 4), 'p': p,
        'V_cramer': round(v, 4),
        'Sig': 'Evet' if p < 0.05 else 'Hayir'
    })
    print(f"  {cat} x GodClass: chi2={chi2:.4f}, p={p:.6f}, V={v:.4f}")

chi2_df = pd.DataFrame(chi2_results)
chi2_df.to_csv(f"{CHARTS_DIR}/chi2_results.csv", index=False)

# Çapraz tablolar
for cat in cat_cols_quality[:2]:
    fig, ax = plt.subplots(figsize=(10, 6))
    ct_vis = pd.crosstab(df[cat].fillna('MISSING'), df['GodClass'])
    ct_vis.plot(kind='bar', ax=ax, color=['#2ecc71', '#e74c3c'], edgecolor='black')
    ax.set_title(f'{cat} x GodClass Capraz Tablosu', fontsize=14, fontweight='bold')
    ax.set_xlabel(cat)
    ax.set_ylabel('Frekans')
    ax.legend(['Non-GodClass (0)', 'GodClass (1)'])
    plt.xticks(rotation=0)
    plt.tight_layout()
    safe = cat.replace(' ', '_').lower()
    plt.savefig(f"{CHARTS_DIR}/crosstab_{safe}_vs_godclass.png", dpi=150, bbox_inches='tight')
    plt.close()

# ============================================================
# BÖLÜM 6.3: ANOVA
# ============================================================
print("\n=== ANOVA (Sayisal ~ GodClass) ===")
anova_results = []
for col in key_metrics:
    groups = [g.dropna() for _, g in df.groupby('GodClass')[col]]
    if len(groups) == 2 and all(len(g) > 0 for g in groups):
        f_stat, p_val = stats.f_oneway(*groups)
        anova_results.append({
            'Degisken': col,
            'F': round(f_stat, 4),
            'p': p_val,
            'Sig': 'Evet' if p_val < 0.05 else 'Hayir'
        })
        print(f"  {col}: F={f_stat:.4f}, p={p_val:.6f}")

anova_df = pd.DataFrame(anova_results)
anova_df.to_csv(f"{CHARTS_DIR}/anova_results.csv", index=False)

# Top ANOVA boxplot
top_anova = anova_df.sort_values('F', ascending=False).head(6)['Degisken'].tolist()
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
for idx, col in enumerate(top_anova):
    ax = axes[idx // 3][idx % 3]
    d0 = df[df['GodClass'] == 0][col].dropna()
    d1 = df[df['GodClass'] == 1][col].dropna()
    bp = ax.boxplot([d0, d1], labels=['Non-GodClass', 'GodClass'], patch_artist=True)
    bp['boxes'][0].set_facecolor('#2ecc71')
    bp['boxes'][1].set_facecolor('#e74c3c')
    ax.set_title(f'{col}', fontsize=12, fontweight='bold')
    ax.set_ylabel(col)
plt.suptitle('En Anlamli Degiskenler ~ GodClass (ANOVA)', fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/numeric_by_godclass.png", dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# BÖLÜM 7: VIF
# ============================================================
print("\n=== VIF ANALİZİ ===")
vif_cols = [c for c in key_metrics if c not in ['LOC.1', 'WMC.1']]
vif_data = df[vif_cols].dropna()
if len(vif_data) > 50000:
    vif_data = vif_data.sample(50000, random_state=42)

scaler_v = StandardScaler()
vif_scaled = pd.DataFrame(scaler_v.fit_transform(vif_data), columns=vif_cols)

vif_results = []
for i, col in enumerate(vif_cols):
    v = variance_inflation_factor(vif_scaled.values, i)
    vif_results.append({
        'Degisken': col, 'VIF': round(v, 4),
        'Ciddi': 'Evet' if v > 10 else 'Hayir',
        'Orta': 'Evet' if v > 5 else 'Hayir'
    })
    print(f"  {col}: VIF={v:.4f}")

vif_df = pd.DataFrame(vif_results)
vif_df.to_csv(f"{CHARTS_DIR}/vif_results.csv", index=False)

fig, ax = plt.subplots(figsize=(14, 7))
colors_vif = ['#e74c3c' if v > 10 else '#f39c12' if v > 5 else '#2ecc71' for v in vif_df['VIF']]
bars = ax.barh(vif_df['Degisken'], vif_df['VIF'], color=colors_vif, edgecolor='black')
ax.axvline(x=10, color='red', linestyle='--', linewidth=2, label='Ciddi MC (VIF=10)')
ax.axvline(x=5, color='orange', linestyle='--', linewidth=2, label='Orta MC (VIF=5)')
ax.set_title('VIF Analizi', fontsize=14, fontweight='bold')
ax.set_xlabel('VIF Degeri')
ax.legend()
for bar, val in zip(bars, vif_df['VIF']):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f'{val:.2f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/vif_analysis.png", dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# BÖLÜM 8: PCA
# ============================================================
print("\n=== PCA ===")
pca_data = df[vif_cols].dropna()
if len(pca_data) > 50000:
    pca_sample = pca_data.sample(50000, random_state=42)
else:
    pca_sample = pca_data

sc_pca = StandardScaler()
X_pca = sc_pca.fit_transform(pca_sample)
pca = PCA()
pca.fit(X_pca)

ev = pca.explained_variance_ratio_ * 100
cum = np.cumsum(ev)
for i, (e, c) in enumerate(zip(ev, cum)):
    print(f"  PC{i+1}: {e:.2f}% (Kum: {c:.2f}%)")

n85 = int(np.argmax(cum >= 85) + 1)
n90 = int(np.argmax(cum >= 90) + 1)
n95 = int(np.argmax(cum >= 95) + 1)
print(f"%85: {n85}, %90: {n90}, %95: {n95}")

# Save PCA data
pca_table = pd.DataFrame({
    'Bilesen': [f'PC{i+1}' for i in range(len(ev))],
    'Varyans': [round(e, 2) for e in ev],
    'Kumulatif': [round(c, 2) for c in cum]
})
pca_table.to_csv(f"{CHARTS_DIR}/pca_results.csv", index=False)

fig, ax = plt.subplots(figsize=(12, 6))
n_comp = len(ev)
ax.bar(range(1, n_comp+1), ev, alpha=0.7, color='#4C72B0', label='Bireysel', edgecolor='black')
ax.plot(range(1, n_comp+1), cum, 'ro-', linewidth=2, label='Kumulatif')
ax.axhline(y=85, color='green', linestyle='--', alpha=0.7, label='%85')
ax.axhline(y=90, color='orange', linestyle='--', alpha=0.7, label='%90')
ax.axhline(y=95, color='red', linestyle='--', alpha=0.7, label='%95')
ax.set_xlabel('Bilesen Numarasi')
ax.set_ylabel('Aciklanan Varyans (%)')
ax.set_title('PCA Scree Plot', fontsize=14, fontweight='bold')
ax.legend()
ax.set_xticks(range(1, n_comp+1))
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/pca_scree_plot.png", dpi=150, bbox_inches='tight')
plt.close()

# PCA 2D
pca_2d = PCA(n_components=2)
comp_2d = pca_2d.fit_transform(X_pca)
gc_labels = df.loc[pca_sample.index, 'GodClass'].values

fig, ax = plt.subplots(figsize=(10, 8))
scatter = ax.scatter(comp_2d[:, 0], comp_2d[:, 1], c=gc_labels, cmap='RdYlGn_r', alpha=0.3, s=5)
plt.colorbar(scatter, ax=ax, label='GodClass')
ax.set_xlabel(f'PC1 ({pca_2d.explained_variance_ratio_[0]*100:.2f}%)')
ax.set_ylabel(f'PC2 ({pca_2d.explained_variance_ratio_[1]*100:.2f}%)')
ax.set_title('PCA 2D Scatter Plot (GodClass ile Renklendirilmis)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/pca_scatter_2d.png", dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# VERİ KALİTESİ ÖZETİ
# ============================================================
print("\n=== VERİ KALİTESİ ===")
print(f"Toplam satir: {len(df)}")
print(f"Duplicate: {df.duplicated().sum()}")
missing = df.isnull().sum()
mp = (missing / len(df) * 100).round(2)
for c in missing.index:
    if missing[c] > 0:
        print(f"  {c}: {missing[c]} ({mp[c]}%)")

# Dosya boyutları ve toplam veri
cs_files = glob.glob(os.path.join(BASE, 'codesmells', 'csv', '*', '*.csv'))
qa_files = glob.glob(os.path.join(BASE, 'quality_attributes', '*', '*.csv'))
cs_total = sum(os.path.getsize(f) for f in cs_files) / 1024 / 1024
qa_total = sum(os.path.getsize(f) for f in qa_files) / 1024 / 1024
main_size = os.path.getsize(os.path.join(BASE, 'resulted', 'class_level_quality_code_smell_mdi.csv')) / 1024 / 1024
print(f"\nDosya boyutlari:")
print(f"  resulted/main csv: {main_size:.2f} MB")
print(f"  codesmells ({len(cs_files)} files): {cs_total:.2f} MB")
print(f"  quality_attributes ({len(qa_files)} files): {qa_total:.2f} MB")
print(f"  Toplam: {main_size + cs_total + qa_total:.2f} MB")

# GodClass proje bazli
print("\n=== GodClass Proje Bazli ===")
gc_proj = df.groupby('project')['GodClass'].agg(['sum', 'count', 'mean'])
gc_proj.columns = ['GodClass_Count', 'Total', 'Rate']
gc_proj['Rate'] = (gc_proj['Rate'] * 100).round(2)
print(gc_proj.to_string())

# GodClass by project chart
fig, ax = plt.subplots(figsize=(12, 6))
gc_proj_sorted = gc_proj.sort_values('Rate', ascending=True)
bars = ax.barh(gc_proj_sorted.index, gc_proj_sorted['Rate'],
               color=sns.color_palette('YlOrRd', len(gc_proj_sorted)), edgecolor='black')
for bar, val in zip(bars, gc_proj_sorted['Rate']):
    ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
            f'{val:.1f}%', va='center', fontsize=10)
ax.set_title('Proje Bazli GodClass Orani (%)', fontsize=14, fontweight='bold')
ax.set_xlabel('GodClass Orani (%)')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/godclass_by_project.png", dpi=150, bbox_inches='tight')
plt.close()

print("\n=== ANALİZ TAMAMLANDI ===")
print(f"Tum grafikler '{CHARTS_DIR}/' dizinine kaydedildi.")

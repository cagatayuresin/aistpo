"""
Code Metrics Dataset SoftwareProjectStructure - Kapsamlı Analiz
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
import os
import warnings
warnings.filterwarnings('ignore')

# Matplotlib Türkçe karakter desteği
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.max_open_warning'] = 50

CHARTS_DIR = "charts_code_metrics"
os.makedirs(CHARTS_DIR, exist_ok=True)

# --- VERİ YÜKLEME ---
print("Veri yükleniyor...")
df_nt = pd.read_csv("datasets/CodeMetricsDatasetSoftwareProjectStructure/OnlyNonTrivial_dt.csv")
df_t = pd.read_csv("datasets/CodeMetricsDatasetSoftwareProjectStructure/OnlyTrivial_dt.csv")

# Birleştirilmiş veri seti
df_nt['dataset'] = 'NonTrivial'
df_t['dataset'] = 'Trivial'
df = pd.concat([df_nt, df_t], ignore_index=True)

print(f"NonTrivial: {df_nt.shape}")
print(f"Trivial: {df_t.shape}")
print(f"Birleşik: {df.shape}")

# Sayısal sütunlar (hedef ve kategorik hariç)
numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != 'refactoring']
# Analiz için önemli metrikler
key_metrics = ['cbo', 'cboModified', 'fanin', 'fanout', 'wmc', 'dit', 'noc', 'rfc',
               'lcom', 'loc', 'totalMethodsQty', 'totalFieldsQty', 'nosi',
               'returnQty', 'loopQty', 'comparisonsQty', 'variablesQty',
               'maxNestedBlocksQty', 'uniqueWordsQty']

# ============================================================
# BÖLÜM 3: BETİMLEYİCİ İSTATİSTİKLER
# ============================================================
print("\n=== BETİMLEYİCİ İSTATİSTİKLER ===")
stats_data = []
for col in key_metrics:
    s = df[col].dropna()
    stats_data.append({
        'Değişken': col,
        'Ortalama': round(s.mean(), 4),
        'Medyan': round(s.median(), 4),
        'Std Sapma': round(s.std(), 4),
        'Min': s.min(),
        'Max': s.max(),
        'Çarpıklık': round(s.skew(), 4),
        'Basıklık': round(s.kurtosis(), 4),
        'Q1': round(s.quantile(0.25), 4),
        'Q3': round(s.quantile(0.75), 4),
        'IQR': round(s.quantile(0.75) - s.quantile(0.25), 4),
    })

stats_df = pd.DataFrame(stats_data)
print(stats_df.to_string(index=False))
stats_df.to_csv(f"{CHARTS_DIR}/descriptive_stats.csv", index=False)

# ============================================================
# BÖLÜM 4: DAĞILIM ANALİZİ - Histogram + Boxplot + Outlier
# ============================================================
print("\n=== DAĞILIM ANALİZİ ===")
outlier_data = []

for col in key_metrics:
    s = df[col].dropna()
    Q1 = s.quantile(0.25)
    Q3 = s.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = ((s < lower) | (s > upper)).sum()
    outlier_pct = round(outliers / len(s) * 100, 2)
    outlier_data.append({
        'Değişken': col,
        'Alt Sınır': round(lower, 2),
        'Üst Sınır': round(upper, 2),
        'Outlier Sayısı': outliers,
        'Oran (%)': outlier_pct
    })

    # Histogram + Boxplot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Histogram
    ax1.hist(s, bins=50, color='#4C72B0', edgecolor='black', alpha=0.7)
    ax1.axvline(s.mean(), color='red', linestyle='--', label=f'Ortalama: {s.mean():.2f}')
    ax1.axvline(s.median(), color='green', linestyle='--', label=f'Medyan: {s.median():.2f}')
    ax1.set_title(f'{col} - Histogram', fontsize=13, fontweight='bold')
    ax1.set_xlabel(col)
    ax1.set_ylabel('Frekans')
    ax1.legend()
    
    # Boxplot
    bp = ax2.boxplot(s, vert=True, patch_artist=True,
                     boxprops=dict(facecolor='#4C72B0', alpha=0.7),
                     medianprops=dict(color='red', linewidth=2))
    ax2.set_title(f'{col} - Boxplot', fontsize=13, fontweight='bold')
    ax2.set_ylabel(col)
    ax2.text(1.15, s.median(), f'Medyan: {s.median():.2f}', fontsize=9, color='red')
    
    plt.tight_layout()
    plt.savefig(f"{CHARTS_DIR}/dist_{col}.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  {col}: Outlier={outliers} ({outlier_pct}%)")

outlier_df = pd.DataFrame(outlier_data)
outlier_df.to_csv(f"{CHARTS_DIR}/outlier_analysis.csv", index=False)

# Genel boxplot - normalize
fig, ax = plt.subplots(figsize=(16, 8))
scaler = StandardScaler()
normalized = pd.DataFrame(scaler.fit_transform(df[key_metrics].dropna()),
                          columns=key_metrics)
normalized.boxplot(ax=ax, rot=45)
ax.set_title("Tüm Anahtar Metriklerin Boxplot Karşılaştırması (Standardize)", fontsize=14, fontweight='bold')
ax.set_ylabel("Standardize Değer")
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/boxplot_all_numeric.png", dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# BÖLÜM 5: HEDEF DEĞİŞKEN ANALİZİ (SINIF DENGESİ)
# ============================================================
print("\n=== SINIF DENGESİ ANALİZİ ===")

# refactoring (birleşik)
ref_counts = df['refactoring'].value_counts()
print(f"refactoring dağılımı:\n{ref_counts}")
majority = ref_counts.max()
minority = ref_counts.min()
imbalance_ratio = majority / minority
print(f"Imbalance ratio: {imbalance_ratio:.4f}")

fig, ax = plt.subplots(figsize=(8, 6))
colors = ['#2ecc71', '#e74c3c']
bars = ax.bar(['Refactoring (1)', 'Non-Refactoring (0)'],
              [ref_counts.get(1, 0), ref_counts.get(0, 0)],
              color=colors, edgecolor='black')
for bar, val in zip(bars, [ref_counts.get(1, 0), ref_counts.get(0, 0)]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
            f'{val:,}\n({val/len(df)*100:.1f}%)',
            ha='center', va='bottom', fontsize=12, fontweight='bold')
ax.set_title('Refactoring Hedef Değişken Sınıf Dağılımı\n(Birleşik Veri Seti)', fontsize=14, fontweight='bold')
ax.set_ylabel('Frekans')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/class_balance_refactoring.png", dpi=150, bbox_inches='tight')
plt.close()

# NonTrivial vs Trivial ayrı ayrı
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
for ax, name, data in [(ax1, 'NonTrivial', df_nt), (ax2, 'Trivial', df_t)]:
    vc = data['refactoring'].value_counts()
    bars = ax.bar(['Refactoring (1)', 'Non-Refactoring (0)'],
                  [vc.get(1, 0), vc.get(0, 0)],
                  color=colors, edgecolor='black')
    for bar, val in zip(bars, [vc.get(1, 0), vc.get(0, 0)]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{val:,}\n({val/len(data)*100:.1f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax.set_title(f'{name} - Refactoring Dağılımı', fontsize=13, fontweight='bold')
    ax.set_ylabel('Frekans')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/class_balance_by_dataset.png", dpi=150, bbox_inches='tight')
plt.close()

# type kategorik dağılım
fig, ax = plt.subplots(figsize=(10, 6))
type_counts = df['type'].value_counts()
bars = ax.bar(type_counts.index, type_counts.values, color=sns.color_palette('Set2', len(type_counts)), edgecolor='black')
for bar, val in zip(bars, type_counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
            f'{val:,}\n({val/len(df)*100:.1f}%)',
            ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_title('Sınıf Tipi (type) Dağılımı', fontsize=14, fontweight='bold')
ax.set_ylabel('Frekans')
ax.set_xlabel('Tip')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/bar_type.png", dpi=150, bbox_inches='tight')
plt.close()

# dataset dağılımı
fig, ax = plt.subplots(figsize=(8, 6))
ds_counts = df['dataset'].value_counts()
bars = ax.bar(ds_counts.index, ds_counts.values, color=['#3498db', '#e67e22'], edgecolor='black')
for bar, val in zip(bars, ds_counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
            f'{val:,}\n({val/len(df)*100:.1f}%)',
            ha='center', va='bottom', fontsize=12, fontweight='bold')
ax.set_title('Veri Seti Kaynak Dağılımı (NonTrivial vs Trivial)', fontsize=14, fontweight='bold')
ax.set_ylabel('Frekans')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/bar_dataset.png", dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# BÖLÜM 6: KORELASYON ANALİZİ
# ============================================================
print("\n=== KORELASYON ANALİZİ ===")
corr_matrix = df[key_metrics].corr()

# Heatmap
fig, ax = plt.subplots(figsize=(18, 14))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
            center=0, square=True, linewidths=0.5, ax=ax,
            annot_kws={'size': 7},
            vmin=-1, vmax=1)
ax.set_title('Pearson Korelasyon Matrisi (Anahtar Metrikler)', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/correlation_heatmap.png", dpi=150, bbox_inches='tight')
plt.close()

# En yüksek korelasyonlar
corr_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr_pairs.append({
            'Değişken 1': corr_matrix.columns[i],
            'Değişken 2': corr_matrix.columns[j],
            'Korelasyon': round(corr_matrix.iloc[i, j], 4)
        })
corr_pairs_df = pd.DataFrame(corr_pairs).sort_values('Korelasyon', key=abs, ascending=False)
print("En yüksek 15 korelasyon:")
print(corr_pairs_df.head(15).to_string(index=False))

# ============================================================
# BÖLÜM 6.2: CHI-SQUARE TESTİ (Kategorik)
# ============================================================
print("\n=== CHI-SQUARE TESTLERİ ===")
cat_cols = ['type', 'dataset']
chi2_results = []
for i, c1 in enumerate(cat_cols):
    for c2 in ['refactoring']:
        ct = pd.crosstab(df[c1], df[c2])
        chi2, p, dof, expected = stats.chi2_contingency(ct)
        n = ct.sum().sum()
        k = min(ct.shape) - 1
        cramers_v = np.sqrt(chi2 / (n * k)) if k > 0 else 0
        chi2_results.append({
            'Değişken 1': c1,
            'Değişken 2': c2,
            'χ²': round(chi2, 4),
            'p-değeri': p,
            'Cramérs V': round(cramers_v, 4),
            'Anlamlı?': 'Evet' if p < 0.05 else 'Hayır'
        })
        print(f"  {c1} × {c2}: χ²={chi2:.4f}, p={p:.6f}, V={cramers_v:.4f}")

# type vs dataset
ct2 = pd.crosstab(df['type'], df['dataset'])
chi2_2, p_2, dof_2, expected_2 = stats.chi2_contingency(ct2)
n_2 = ct2.sum().sum()
k_2 = min(ct2.shape) - 1
cramers_v_2 = np.sqrt(chi2_2 / (n_2 * k_2)) if k_2 > 0 else 0
chi2_results.append({
    'Değişken 1': 'type',
    'Değişken 2': 'dataset',
    'χ²': round(chi2_2, 4),
    'p-değeri': p_2,
    'Cramérs V': round(cramers_v_2, 4),
    'Anlamlı?': 'Evet' if p_2 < 0.05 else 'Hayır'
})

chi2_df = pd.DataFrame(chi2_results)
chi2_df.to_csv(f"{CHARTS_DIR}/chi2_results.csv", index=False)

# Çapraz tablolar
fig, ax = plt.subplots(figsize=(10, 6))
ct_vis = pd.crosstab(df['type'], df['refactoring'])
ct_vis.plot(kind='bar', ax=ax, color=['#e74c3c', '#2ecc71'], edgecolor='black')
ax.set_title('type × refactoring Çapraz Tablosu', fontsize=14, fontweight='bold')
ax.set_xlabel('Tip')
ax.set_ylabel('Frekans')
ax.legend(['Non-Refactoring (0)', 'Refactoring (1)'])
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/crosstab_type_vs_refactoring.png", dpi=150, bbox_inches='tight')
plt.close()

fig, ax = plt.subplots(figsize=(10, 6))
ct_vis2 = pd.crosstab(df['dataset'], df['refactoring'])
ct_vis2.plot(kind='bar', ax=ax, color=['#e74c3c', '#2ecc71'], edgecolor='black')
ax.set_title('dataset × refactoring Çapraz Tablosu', fontsize=14, fontweight='bold')
ax.set_xlabel('Veri Seti')
ax.set_ylabel('Frekans')
ax.legend(['Non-Refactoring (0)', 'Refactoring (1)'])
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/crosstab_dataset_vs_refactoring.png", dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# BÖLÜM 6.3: ANOVA (Sayısal ~ Refactoring)
# ============================================================
print("\n=== ANOVA TESTİ (Sayısal ~ refactoring) ===")
anova_results = []
for col in key_metrics:
    groups = [g.dropna() for _, g in df.groupby('refactoring')[col]]
    if len(groups) == 2 and all(len(g) > 0 for g in groups):
        f_stat, p_val = stats.f_oneway(*groups)
        anova_results.append({
            'Değişken': col,
            'F-İstatistik': round(f_stat, 4),
            'p-değeri': p_val,
            'Anlamlı?': 'Evet' if p_val < 0.05 else 'Hayır'
        })
        print(f"  {col}: F={f_stat:.4f}, p={p_val:.6f}")

anova_df = pd.DataFrame(anova_results)
anova_df.to_csv(f"{CHARTS_DIR}/anova_results.csv", index=False)

# Sayısal ~ refactoring boxplot (seçili metrikler)
top_anova = anova_df.sort_values('F-İstatistik', ascending=False).head(6)['Değişken'].tolist()
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
for idx, col in enumerate(top_anova):
    ax = axes[idx // 3][idx % 3]
    data_0 = df[df['refactoring'] == 0][col].dropna()
    data_1 = df[df['refactoring'] == 1][col].dropna()
    bp = ax.boxplot([data_0, data_1], labels=['Non-Refact.', 'Refactoring'],
                    patch_artist=True)
    bp['boxes'][0].set_facecolor('#e74c3c')
    bp['boxes'][1].set_facecolor('#2ecc71')
    ax.set_title(f'{col}', fontsize=12, fontweight='bold')
    ax.set_ylabel(col)
plt.suptitle('En Anlamlı Değişkenler ~ Refactoring (ANOVA)', fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/numeric_by_refactoring.png", dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# BÖLÜM 7: MULTİCOLLİNEARİTY (VIF)
# ============================================================
print("\n=== VIF ANALİZİ ===")
vif_cols = ['cbo', 'fanin', 'fanout', 'wmc', 'dit', 'noc', 'rfc', 'lcom',
            'loc', 'totalMethodsQty', 'totalFieldsQty', 'nosi',
            'returnQty', 'loopQty', 'comparisonsQty', 'variablesQty',
            'maxNestedBlocksQty', 'uniqueWordsQty']
vif_data = df[vif_cols].dropna()
# sample if too large
if len(vif_data) > 100000:
    vif_data = vif_data.sample(100000, random_state=42)

scaler_vif = StandardScaler()
vif_scaled = pd.DataFrame(scaler_vif.fit_transform(vif_data), columns=vif_cols)

vif_results = []
for i, col in enumerate(vif_cols):
    vif_val = variance_inflation_factor(vif_scaled.values, i)
    vif_results.append({
        'Değişken': col,
        'VIF': round(vif_val, 4),
        'Ciddi MC? (>10)': 'Evet' if vif_val > 10 else 'Hayır',
        'Orta MC? (>5)': 'Evet' if vif_val > 5 else 'Hayır'
    })
    print(f"  {col}: VIF={vif_val:.4f}")

vif_df = pd.DataFrame(vif_results)
vif_df.to_csv(f"{CHARTS_DIR}/vif_results.csv", index=False)

fig, ax = plt.subplots(figsize=(14, 7))
colors_vif = ['#e74c3c' if v > 10 else '#f39c12' if v > 5 else '#2ecc71' for v in vif_df['VIF']]
bars = ax.barh(vif_df['Değişken'], vif_df['VIF'], color=colors_vif, edgecolor='black')
ax.axvline(x=10, color='red', linestyle='--', linewidth=2, label='Ciddi MC (VIF=10)')
ax.axvline(x=5, color='orange', linestyle='--', linewidth=2, label='Orta MC (VIF=5)')
ax.set_title('VIF (Variance Inflation Factor) Analizi', fontsize=14, fontweight='bold')
ax.set_xlabel('VIF Değeri')
ax.legend()
for bar, val in zip(bars, vif_df['VIF']):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f'{val:.2f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/vif_analysis.png", dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# BÖLÜM 8: PCA ANALİZİ
# ============================================================
print("\n=== PCA ANALİZİ ===")
pca_cols = vif_cols  # same numeric cols
pca_data = df[pca_cols].dropna()
if len(pca_data) > 100000:
    pca_data_sample = pca_data.sample(100000, random_state=42)
else:
    pca_data_sample = pca_data

scaler_pca = StandardScaler()
pca_scaled = scaler_pca.fit_transform(pca_data_sample)

pca = PCA()
pca.fit(pca_scaled)

explained = pca.explained_variance_ratio_ * 100
cumulative = np.cumsum(explained)

print("PCA Sonuçları:")
for i, (e, c) in enumerate(zip(explained, cumulative)):
    print(f"  PC{i+1}: {e:.2f}% (Kümülatif: {c:.2f}%)")

n_85 = np.argmax(cumulative >= 85) + 1
n_90 = np.argmax(cumulative >= 90) + 1
n_95 = np.argmax(cumulative >= 95) + 1
print(f"%85 varyans: {n_85} bileşen")
print(f"%90 varyans: {n_90} bileşen")
print(f"%95 varyans: {n_95} bileşen")

# Scree plot
fig, ax = plt.subplots(figsize=(12, 6))
n_comp = len(explained)
ax.bar(range(1, n_comp+1), explained, alpha=0.7, color='#4C72B0', label='Bireysel', edgecolor='black')
ax.plot(range(1, n_comp+1), cumulative, 'ro-', linewidth=2, label='Kümülatif')
ax.axhline(y=85, color='green', linestyle='--', alpha=0.7, label='%85 eşik')
ax.axhline(y=90, color='orange', linestyle='--', alpha=0.7, label='%90 eşik')
ax.axhline(y=95, color='red', linestyle='--', alpha=0.7, label='%95 eşik')
ax.set_xlabel('Bileşen Numarası')
ax.set_ylabel('Açıklanan Varyans (%)')
ax.set_title('PCA Scree Plot', fontsize=14, fontweight='bold')
ax.legend()
ax.set_xticks(range(1, n_comp+1))
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/pca_scree_plot.png", dpi=150, bbox_inches='tight')
plt.close()

# PCA 2D scatter
pca_2d = PCA(n_components=2)
components_2d = pca_2d.fit_transform(pca_scaled)
ref_labels = df.loc[pca_data_sample.index, 'refactoring'].values

fig, ax = plt.subplots(figsize=(10, 8))
scatter = ax.scatter(components_2d[:, 0], components_2d[:, 1],
                     c=ref_labels, cmap='RdYlGn', alpha=0.3, s=5)
plt.colorbar(scatter, ax=ax, label='Refactoring')
ax.set_xlabel(f'PC1 ({pca_2d.explained_variance_ratio_[0]*100:.2f}%)')
ax.set_ylabel(f'PC2 ({pca_2d.explained_variance_ratio_[1]*100:.2f}%)')
ax.set_title('PCA 2D Scatter Plot (Refactoring ile Renklendirilmiş)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/pca_scatter_2d.png", dpi=150, bbox_inches='tight')
plt.close()

# ============================================================
# BÖLÜM 9: VERİ KALİTESİ
# ============================================================
print("\n=== VERİ KALİTESİ ===")
print("Eksik değerler (birleşik):")
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
missing_df = pd.DataFrame({'Sütun': missing.index, 'Eksik': missing.values, 'Oran (%)': missing_pct.values})
missing_df = missing_df[missing_df['Eksik'] > 0]
print(missing_df.to_string(index=False))

print(f"\nDuplicate kayıt (birleşik): {df.duplicated().sum()}")
print(f"NonTrivial duplicate: {df_nt.drop(columns='dataset').duplicated().sum()}")
print(f"Trivial duplicate: {df_t.drop(columns='dataset').duplicated().sum()}")

# Feature Scaling
print("\nFeature Scaling Gereksinimi:")
scaling_data = []
for col in key_metrics:
    s = df[col].dropna()
    scaling_data.append({
        'Değişken': col,
        'Min': s.min(),
        'Max': s.max(),
        'Aralık': s.max() - s.min(),
        'Std': round(s.std(), 4)
    })
scaling_df = pd.DataFrame(scaling_data)
print(scaling_df.to_string(index=False))

# ============================================================
# EK: Metrik karşılaştırma NonTrivial vs Trivial
# ============================================================
print("\n=== NONTRIVIAL vs TRIVIAL KARŞILAŞTIRMA ===")
comparison_data = []
for col in key_metrics[:10]:
    nt_mean = df_nt[col].dropna().mean()
    t_mean = df_t[col].dropna().mean()
    comparison_data.append({
        'Değişken': col,
        'NonTrivial Ort.': round(nt_mean, 4),
        'Trivial Ort.': round(t_mean, 4),
        'Fark (%)': round((nt_mean - t_mean) / t_mean * 100, 2) if t_mean != 0 else 'N/A'
    })
comp_df = pd.DataFrame(comparison_data)
print(comp_df.to_string(index=False))

# Karşılaştırma bar chart
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
compare_cols = ['cbo', 'wmc', 'rfc', 'lcom', 'loc', 'totalMethodsQty']
for idx, col in enumerate(compare_cols):
    ax = axes[idx // 3][idx % 3]
    nt_mean = df_nt[col].dropna().mean()
    t_mean = df_t[col].dropna().mean()
    bars = ax.bar(['NonTrivial', 'Trivial'], [nt_mean, t_mean],
                  color=['#3498db', '#e67e22'], edgecolor='black')
    for bar, val in zip(bars, [nt_mean, t_mean]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{val:.2f}', ha='center', va='bottom', fontsize=10)
    ax.set_title(f'{col} Ortalama Karşılaştırma', fontsize=12, fontweight='bold')
    ax.set_ylabel('Ortalama')
plt.suptitle('NonTrivial vs Trivial - Anahtar Metrik Ortalamaları', fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/comparison_nt_vs_t.png", dpi=150, bbox_inches='tight')
plt.close()

print("\n=== ANALİZ TAMAMLANDI ===")
print(f"Tüm grafikler '{CHARTS_DIR}/' dizinine kaydedildi.")

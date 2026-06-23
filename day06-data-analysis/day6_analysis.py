# Day 6 — Letting the Data Push Back
# 5 days of building, no real findings yet.
# Day 6 was the first day I stopped building and started actually
# looking at what the data was saying — stats first, then visualizing
# each result to see if it held up.
# Continues directly from the features_df built in Day 5.

# Stats Analysis

#Do positive earnings gaps continue upward?
positive_gap=features_df[features_df['GapPct']>0]
print("Do positive earnings gaps continue upward?")
print(positive_gap['Return3D'].mean())

#Do high-volume earnings reactions perform better?
features_df['HighVolume']=(features_df['VolumeRatio']>2)
print('Do high-volume earnings reactions perform better?')
print(features_df.groupby('HighVolume')['Return3D'].mean())

#Does bearish NIFTY weaken earnings continuation?
bearish_market=features_df[features_df['Nifty1D_Return']<0]
print('Does bearish NIFTY weaken earnings continuation?')
print(bearish_market['Return1D'].mean())

#Do stocks outperforming NIFTY before earnings continue outperforming?
strong_rs=features_df[features_df['RelativeStrength5D']>0]
print('Do stocks outperforming NIFTY before earnings continue outperforming?')
print(strong_rs['Return3D'].mean())


# Visualization
%pip install seaborn -q
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="whitegrid")

plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=features_df,
    x='GapPct',
    y='Return3D',
    hue='Ticker',
    palette='tab10',
    alpha=0.8
)
plt.title('Earnings Gap vs 3-Day Post-Event Return')
plt.xlabel('Gap %')
plt.ylabel('3-Day Return')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()

(ax1, ax2) = plt.subplots(1, 2)
sns.histplot(features_df['Return3D'], bins=50, kde=True)
sns.boxplot(data=features_df, x='HighVolume', y='Return3D')

features_df.groupby('Date')['Return3D'].mean().cumsum().plot()

# #QuantFinance #AlgoTrading #Python #BuildingInPublic

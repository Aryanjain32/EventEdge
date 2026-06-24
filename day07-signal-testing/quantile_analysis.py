# Day 7 — Testing the Signal
# Finding a pattern is easy. Proving it isn't.
# Relative Strength looked strong out of Day 6, but a convincing chart
# isn't evidence. This script tests every feature the same rigorous way:
# split observations into 5 buckets by feature value, weakest 20% to
# strongest 20%, and check if returns actually separate cleanly across them.
# Continues directly from the features_df built in Day 5.

features_to_validate = [
    'RelativeStrength1D',  # Post-event single day reaction alpha
    'RelativeStrength5D',  # Pre-event momentum accumulation alpha
    'GapPct',              # Overnight price shock intensity
    'VolumeRatio',         # Institutional commitment indicator
    'PreEventReturn',      # Pre-event absolute momentum trend
    'Nifty1D_Return',      # Broad market performance environment
]      

quantile_lables=['Bottom 20%', "20%-40%", '40%-60%', '60%-80%', 'Top 20%']

# 3. Process each feature independently
for column in features_to_validate:
    if column in features_df.columns:
        print(f"\n📊 Performance Breakdown for Factor: {column}")
        # Slice the data into 5 equal groups based on ranked value distribution
        if features_df[column].nunique()>=5:
            features_df['Quantile_Bucket']=pd.qcut(
                features_df[column],
                q=5,
                labels=quantile_lables,
                duplicates='drop'

            )
            performance_summary =features_df.groupby('Quantile_Bucket',observed=False)['Return3D'].mean()*100
            performance_df = performance_summary.to_frame(name='Avg_Future_3D_Return_%')
            
            print(performance_df)
            if len(performance_df) == 5:
                factor_spread = performance_df.loc['Top 20%', 'Avg_Future_3D_Return_%'] - performance_df.loc['Bottom 20%', 'Avg_Future_3D_Return_%']
                print(f"🏁 Alpha Spread (Top vs Btm Quintile): {factor_spread:+.2f}%")
        else:
            print(f"⚠️ Not enough unique observations in column '{column}' to distribute across 5 quintiles.")
    else:
        print(f"❌ Error: Column '{column}' was not found inside your features_df structure.")

# 4. Clean up the temporary validation column to leave your original dataframe pristine
if 'Quantile_Bucket' in features_df.columns:
    features_df = features_df.drop(columns=['Quantile_Bucket'])

# #QuantFinance #AlgoTrading #Python #BuildingInPublic

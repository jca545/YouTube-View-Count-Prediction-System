import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from scipy.stats import linregress
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

#==================================================
#  Global Variables
#==================================================
# Mapping dicts
DICT = {}

# HERE: change these are optional
# Input Data path
INPUT = "inputs/ALL.csv"

# Video to predict
TO_PREDICT = {
    'duration_sec': 99,
    'channelSubs': 448_0000,
    'style': 'KPop',            # categorical
    'type': 'Cover',            # categorical
    'season': 'Summer',         # categorical
    'dayOfWeek': 'Friday',      # categorical
    'weeks_since_published': 3 
}



#==================================================
#  HELPER FUNCTIONS
#==================================================
# --------------------------------------------------
# ↓ PROCESSING: 'type, season, dayOfWeek' to rank ↓ 
# --------------------------------------------------
"""
input:
    1) df: dataframe
output:
    df: dataframe, replaced with ranked style
"""
def style_rank(df):
    styleRank =  df.groupby(['style'])['views'].mean().reset_index(name='means')
    styleRank['rank'] = styleRank['means'].rank(method='dense').astype(int)
    # Create mapping from style to rank
    style_to_rank_dict = styleRank.set_index('style')['rank'].to_dict()
    # add mapping to dict
    DICT['style'] = style_to_rank_dict
    # add rank values to df 
    df['style'] = df['style'].map(style_to_rank_dict)

    return df


# --------------------------------------------------
# ↓ PROCESSING: 'type, season, dayOfWeek' to rank ↓ 
# --------------------------------------------------
"""
input:
    1) df: dataframe
    2) col: string, column of the dataframe
output:
    df: dataframe, + ranked col (numerical), - col (category)
"""
def other_rank(df, col):
    # mean view for each channel's "col"
    colRank = df.groupby(['channelId', col])['views'].mean().reset_index(name='means')
    # rank the mean view within each channel
    colRank['rank_within_channel'] = colRank.groupby('channelId')['means'].rank(method='dense').astype(int)
    # sum of ranks accross data
    rankSum = colRank.groupby(col)['rank_within_channel'].sum().reset_index(name='sum_ranks')
    # standardize the "col"'s Rank
    rankSum['standard_rank'] = rankSum['sum_ranks'].rank(method='dense').astype(int)
    # Create mapping from type to standard_rank
    rank_dict = rankSum.set_index(col)['standard_rank'].to_dict()
    # add mapping to dictionary
    DICT[col] = rank_dict
    # add rank values to df
    df[col] = df[col].map(rank_dict)

    # return ranked-DF
    return df
# --------------------------------------------------


# --------------------------------------------------
# ↓ PROCESSING: ALL categorical to rank ↓
# --------------------------------------------------
def to_rank(df):
    # Style
    df = style_rank(df)

    #type, season, dayOfWeek
    categories = ['type', 'season', 'dayOfWeek']
    for c in categories:
        df = other_rank(df, c)

    # channel not important anymore
    df = df.drop(columns=["channelId"])
   
    return df
# --------------------------------------------------


# --------------------------------------------------
#  ↓ PROCESSING: + col: weeks since published ↓ 
# --------------------------------------------------
"""
Add a column for the amount of weeks since the video is published
    'weeks_since_published'
"""
def weeks_published(df):
    # Convert publishedAt to datetime and remove timezone
    df['publishedAt'] = pd.to_datetime(df['publishedAt'], errors='coerce').dt.tz_convert(None)
    # Calculate weeks since published
    now = pd.Timestamp.today()
    diff_secs = (now - df['publishedAt']).dt.total_seconds()
    # secs to week: 60s=1min,  60min=1hr,  24hr=1d,  7d=1week
    # consider the week of publish as w1
    df['weeks_since_published'] = (diff_secs / (3600 * 24 * 7)).clip(lower=1).astype(float)
    # drop unneed features
    df = df.drop(columns=['publishedAt'])

    return df
# --------------------------------------------------


# --------------------------------------------------
#  ↓ PROCESSING: Raw data ↓ 
# --------------------------------------------------
"""
input: df from read input file
output: cleaned df
"""
def process_data(df):
    # Drop features not helpful
    df = df.drop(columns=["title", "likes", "comments", "engagment"])

    # convert categorical col's val to numerical rank
    df = to_rank(df)

    # Add col: 'weeks_since_published'
    df = weeks_published(df)

    # views right skewed n___ => natural log (since view can have 0)
    df['views'] = np.log1p(df['views'])

    return df
# --------------------------------------------------


# --------------------------------------------------
#  ↓ PLOT: Actual v.s. Predicted views ↓ 
# --------------------------------------------------
def plot_performance(y_test, y_pred):
    # Convert back from log1p to original scale
    actual_views = np.expm1(y_test)
    predicted_views = np.expm1(y_pred)

    plt.figure(figsize=(12, 6))
    plt.plot(actual_views.values, label='Actual Views', marker='o')
    plt.plot(predicted_views, label='Predicted Views', marker='x')
    
    plt.xlabel("Sample index")
    plt.ylabel("Views")
    plt.title("Actual vs Predicted Views")
    plt.legend()
    plt.tight_layout()

    plt.savefig("plots/performance.png")
# --------------------------------------------------


# --------------------------------------------------
#  ↓ MODEL: Train and test ↓ 
# --------------------------------------------------
def train_model(X, y):
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y)

    # Train Random Forest
    model = RandomForestRegressor(
        n_estimators=12,
        max_depth=25, 
        min_samples_leaf=10, 
        random_state=42
    ).fit(X_train, y_train)

    # print model train result
    print(f"Train score: {model.score(X_train, y_train):.4f}")
    # print model test result
    y_pred = model.predict(X_test)
    print(f"Test score: {r2_score(y_test, y_pred):.4f}")

    # visualize performance
    plot_performance(y_test, y_pred)
    
    return model
# --------------------------------------------------



# --------------------------------------------------
#  ↓ PLOT: feature v.s. their importance ↓
# --------------------------------------------------
"""
Plot each feature's importance score on bar plot
    x: feature
    y: importance
"""
def plot_importance(feat_imp):
    plt.figure(figsize=(12,6))
    # code ref from:
    #   https://seaborn.pydata.org/generated/seaborn.barplot.html
    ax = sns.barplot(x='feature', y='importance', data=feat_imp)
    ax.bar_label(ax.containers[0], fontsize=12)
    plt.title("Top 15 Feature Importances")
    plt.tight_layout()
    plt.savefig("plots/importance.png")
# --------------------------------------------------


# --------------------------------------------------
#  ↓ IMPORTANCE: get feature importance ↓
# --------------------------------------------------
"""
input:
    importance: the importance variable from model
    features: all features except 'view'
output:
    feat_imp: df of 'feature', 'importance'
"""
def get_important(importances, features):
    # put importance into df
    feat_imp = pd.DataFrame({'feature': features, 'importance': importances}).sort_values(by='importance', ascending=False)
    print(feat_imp.head(3))

    # barplot top features 
    plot_importance(feat_imp)

    return feat_imp
# --------------------------------------------------


# --------------------------------------------------
#  ↓ PLOT: feature val v.s. views ↓ 
# --------------------------------------------------
"""
Plot the scatter plot with 3 sub-plot
one for each top 3 important feature, 
    x: feature's value
    y: views
    title: feature v.s. view
"""
def plot_scatter(df, top3):
    # plot code ref from: 
    #   https://stackoverflow.com/questions/17210646/python-subplot-within-a-loop-first-panel-appears-in-wrong-position
    _, axes = plt.subplots(1, 3, figsize=(18, 5))
    for i, feat in enumerate(top3):
        ax = axes[i]
        sns.scatterplot(x=df[feat], y=df['views'], ax=ax, alpha=0.5)
        sns.regplot(x=df[feat], y=df['views'], ax=ax, scatter=False, color='red', line_kws={"lw":2})
        ax.set_title(f"{feat} vs Views (log1p)")
        ax.set_xlabel(feat)
        ax.set_ylabel("Log(1 + views)")
    plt.tight_layout()
    plt.savefig('plots/corr.png')
# --------------------------------------------------


# --------------------------------------------------
#  ↓ PLOT: channel's sub v.s. avg view ↓ 
# --------------------------------------------------
def plot_subs(df):
    # Select only needed columns to minimize copying
    df2 = df[['channelSubs', 'views']].copy()
    df2['log_views'] = np.log1p(df2['views'])
    
    # Group by channelSubs, compute average log_views
    grouped = df2.groupby('channelSubs')['log_views'].mean().reset_index()
    
    # Log-transform subscribers for linearity
    log_subs = np.log10(grouped['channelSubs'])
    log_views = grouped['log_views']
    
    # Run linear regression
    slope, intercept, r_value, p_value, std_err = linregress(log_subs, log_views)
    print(f"Slope: {slope:.4f}, Intercept: {intercept:.4f}, R²: {r_value**2:.4f}")
    
    # Generate points for fit line
    x_fit = np.linspace(log_subs.min(), log_subs.max(), 100)
    y_fit = intercept + slope * x_fit

    # scatter plot with best fit line
    plt.figure(figsize=(10,6))
    plt.scatter(grouped['channelSubs'], grouped['log_views'], alpha=0.6, label='Data points')
    plt.plot(10**x_fit, y_fit, color='red', linewidth=2, label='Best fit line')
    plt.title('Average Log Views vs. Channel Subscribers with Best Fit Line')
    plt.xlabel('Channel Subscribers')
    plt.ylabel('Average Log Views')
    plt.xscale('log')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("plots/subs.png")
# --------------------------------------------------


# --------------------------------------------------
#  ↓ PREDICT: the view amount ↓ 
# --------------------------------------------------
"""
input:
    X: all features except 'view
"""
def predict_view(X, model):
    # conver video info to df
    df_new = pd.DataFrame([TO_PREDICT])

    ###----- ↓ process data to match ↓ -----
    # map categorical val
    for c in ['style', 'type', 'season', 'dayOfWeek']:
        mapping = DICT.get(c)
        df_new[c] = df_new[c].map(mapping)
    # find col missing, fill missing with zero
    missing_cols = set(X.columns) - set(df_new.columns)
    for col in missing_cols:
        df_new[col] = 0  
    # Reorder columns to match training features order
    df_new = df_new[X.columns]
    ###----- ↑ process data to match ↑ -----


    ###----- ↓ predict views ↓ -----
    # Predict log views
    predicted_log_views = model.predict(df_new)
    # Convert back to original scale
    predicted_views = np.expm1(predicted_log_views)
    print(f"Predicted views: {predicted_views[0]:,.0f} after {TO_PREDICT['weeks_since_published']} weeks")
    ###----- ↑ predict views ↑ -----
# --------------------------------------------------



#==================================================
#  MAIN PARTS
#==================================================
def main():
    # Load CSV
    df = pd.read_csv(INPUT)

    # plot subs v.s. chanel's avg view
    #plot_subs(df)

    # Process Raw data to what we want
    df = process_data(df)

    # Define features and target
    feature_cols = [col for col in df.columns if col != 'views']
    X = df[feature_cols]
    y = df['views']

    # Train and Test a model
    model = train_model(X, y)

    # Extract importance
    feat_imp = get_important(model.feature_importances_, X.columns)
    # put top 3 important feature name into list
    top3 = feat_imp.head(3)['feature'].tolist()

    # Plot scatter: top3 feature v.s. views
    plot_scatter(df, top3)

    # Predict views of the TO_PREDICT video
    predict_view(X, model)


if __name__ == '__main__':
    main()
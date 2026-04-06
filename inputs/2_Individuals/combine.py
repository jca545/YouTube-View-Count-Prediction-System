import pandas as pd
import os
import glob

# Define schema columns (optional, if you want to ensure column order)
columns = ['style', 'channelId', 'channelSubs', 'title', 'type', 'duration_sec',
           'publishedAt', 'dayOfWeek', 'season', 'views', 'likes', 'comments', 'engagment']

# Get all CSV files in the current directory
csv_files = glob.glob(os.path.join(os.getcwd(), '*.csv'))

# Read and combine all CSVs into one DataFrame
dfs = []
for file in csv_files:
    df = pd.read_csv(file)
    # Optional: ensure the df columns match schema and order
    df = df[columns]  
    dfs.append(df)

combined_df = pd.concat(dfs, ignore_index=True)

# Save combined DataFrame to new CSV file
combined_df.to_csv('ALLCombined.csv', index=False)

print(f"Combined {len(csv_files)} files into ALLCombined.csv")

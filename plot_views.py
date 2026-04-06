import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set()

INPUT = "inputs/ALL.csv"

def plot_views_distribution():
    df = pd.read_csv(INPUT)

    # extract view
    views = df['views']

    # log1p 
    views_log = np.log1p(views)

    plt.figure(figsize=(14,6))

    # left: orig view vs. count
    plt.subplot(1, 2, 1)
    sns.histplot(views, bins=50)
    plt.title('Original Views Distribution')
    plt.xlabel('Views')
    plt.ylabel('Count')

    # right: log1p view vs. count
    plt.subplot(1, 2, 2)
    sns.histplot(views_log, bins=50)
    plt.title('Log(1 + Views) Distribution')
    plt.xlabel('Log(1 + Views)')
    plt.ylabel('Count')

    plt.tight_layout()
    plt.savefig('view_distrib.png')
    plt.show()

if __name__ == '__main__':
    plot_views_distribution()

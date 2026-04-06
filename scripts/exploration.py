import pandas as pd
import numpy as np

df = pd.read_csv('../data/dataset.csv')

print(f"Rows: {df.shape[0]:,}  |  Columns: {df.shape[1]}")
print()
print("All columns:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i:3d}. {col}")
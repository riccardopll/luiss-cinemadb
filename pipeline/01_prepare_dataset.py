from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# Download selected version
data_dir = Path(__file__).resolve().parent / "data"
path = data_dir / "movies.csv"

print("Path to dataset files:", path)
#small dataset visualization
print("Visualizing a small sample of the dataset...")
# Load the dataset into a pandas DataFrame
df = pd.read_csv(path)
# Display the first few rows of the dataset
print(df.head())
#name of columns
print("Columns in the dataset:", df.columns)
#missing values
missing_values = df.isnull().sum()
if missing_values.any():
    print("There are missing values in the dataset.")
    print("Missing values per column:")
    print(missing_values)
    print("Percentage of missing values per column:")
    print((missing_values / len(df)) * 100)
else:
    print("There are no missing values in the dataset.")

# substitute missing values with empty string ""
df.fillna("", inplace=True)
#check 
missing_values_after = df.isnull().sum()
if missing_values_after.any():
    print("There are still missing values in the dataset after filling.")
else:
    print("There are no missing values in the dataset after filling.")
#check no repetition of ids 
if df.duplicated(subset=['id']).any():
    print("There are duplicated movie IDs in the dataset.")
    print("Number of duplicated movie IDs:", df.duplicated(subset=['id']).sum())
#check if the duplicated ids correspond to the same movie
#for each duplicated id, check if the title is the same
duplicated_ids = df[df.duplicated(subset=['id'], keep=False)]

for movie_id, group in duplicated_ids.groupby('id'):
    if group['title'].nunique(dropna=False) > 1:
        print(f"Duplicated movie ID {movie_id} corresponds to different titles:")
        print(group[['id', 'title']])
#eliminate the second occurrence of the duplicated ids
df.drop_duplicates(subset=['id'], keep='first', inplace=True)
#check if the duplicated ids have been eliminated
if df.duplicated(subset=['id']).any():
    print("There are still duplicated movie IDs in the dataset after dropping duplicates.")
else:
    print("There are no duplicated movie IDs in the dataset after dropping duplicates.")





# Save the final DataFrame after this script's cleaning steps.
output_path = data_dir / "df_modified_01.csv"
df.to_csv(output_path, index=False, encoding="utf-8")
print("Modified DataFrame saved to:", output_path)

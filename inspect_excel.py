import pandas as pd

df = pd.read_excel('RAB_Analisis 03 April 2026.xlsx', sheet_name='RAB Sosial Ekonomi Budaya')
pd.set_option('display.max_columns', None)
print(df.head(25).to_string())

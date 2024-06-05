import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

df = st.file_uploader('CSV 파일 업로드', type=['csv'])

print(df.columns)
print(df.dtypes)

df['LOT'] = pd.to_datetime(df['LOT'], format='%Y/%m/%d %H:%M')
df['AET'] = pd.to_datetime(df['AET'], format='%Y/%m/%d %H:%M')

df['AST'] = df['LOT'] + pd.to_timedelta(df['SOL'], unit='m')
df['AST'] = pd.to_datetime(df['AST'], format='%Y/%m/%d %H:%M')

df['WASO'] = pd.to_timedelta(df['WASO'], unit='m')

# Calculate the new column
df['TST'] = (df['AET'] - df['AST'] - pd.to_timedelta(df['WASO'], unit='m'))

df['TST'] = df['TST'].dt.total_seconds() / 60
df['WASO'] = df['WASO'].dt.total_seconds() / 60

# Calculate the new column 'DSE'
df['DSE'] = (pd.to_datetime(df['AET']) - pd.to_datetime(df['LOT']))

# Convert the resulting timedelta to minutes
df['DSE'] = df['DSE'].dt.total_seconds() / 60

df['SE'] = df['TST']/df['DSE']

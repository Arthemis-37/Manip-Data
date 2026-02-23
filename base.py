import pandas as pd
import streamlit as st

df = pd.read_csv('world_energy_consumption.csv')

def classify_pollution(co2):
    if co2 > 1000: return 'Élevé'
    elif co2 > 100: return 'Moyen'
    else: return 'Faible'

df['pollution_level'] = df['co2'].apply(classify_pollution)

df = df.assign(renewables_share_calc = lambda x: (x['renewables_consumption'] / x['primary_energy_consumption']) * 100)

stats_continent = df.groupby('country').agg({
    'primary_energy_consumption': 'sum',
    'renewables_consumption': 'mean',
    'co2': 'std'
}).rename(columns={'co2': 'co2_standard_deviation'})

pollution_counts = df['pollution_level'].value_counts()
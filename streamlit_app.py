import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Tableau de bord énergétique mondial", layout="wide")

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/Arthemis-37/Manip-Data/refs/heads/main/World%20Energy%20Consumption.csv"
    local_csv = Path(__file__).resolve().parent / "world_energy_consumption.csv"
    try:
        df = pd.read_csv(url)
    except Exception:
        df = pd.read_csv(local_csv)

    df_clean = df.dropna(subset=['iso_code']).copy()
    
    cols_to_fix = ['solar_consumption', 'renewables_consumption', 'primary_energy_consumption', 'co2']
    for col in cols_to_fix:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna(0)

    def solar_intensity(val):
        if val > 10: return "Producteur Majeur"
        elif val > 0: return "Producteur Mineur"
        else: return "Non producteur"
    
    df_clean['solar_status'] = df_clean['solar_consumption'].apply(solar_intensity)

    df_clean = df_clean.assign(
        renewables_pct = lambda x: (x['renewables_consumption'] / x['primary_energy_consumption'] * 100).fillna(0)
    )
    
    return df_clean

df = load_data()

st.sidebar.header("Filtres d’exploration")

countries = sorted(df['country'].unique())
country_options = ["Tous les pays"] + countries
selected_country = st.sidebar.selectbox(
    "Sélectionner un pays",
    country_options,
    index=country_options.index("France") if "France" in country_options else 0
)

year_range = st.sidebar.slider("Choisir la période", 
                               int(df['year'].min()), 
                               int(df['year'].max()), 
                               (1990, 2021))

if selected_country == "Tous les pays":
    df_filtered = df[df['year'].between(year_range[0], year_range[1])]
else:
    df_filtered = df[(df['country'] == selected_country) & (df['year'].between(year_range[0], year_range[1]))]

st.title(f"Tableau de bord énergétique — {selected_country}")
st.markdown(f"Période analysée : **{year_range[0]}** à **{year_range[1]}**")

st.subheader("Indicateurs clés")

total_cons = df_filtered['primary_energy_consumption'].sum()
avg_co2 = df_filtered['greenhouse_gas_emissions'].mean()
std_renew = df_filtered['renewables_consumption'].std()

col1, col2, col3 = st.columns(3)
col1.metric("Consommation totale (TWh)", f"{total_cons:,.2f}")
col2.metric("Émissions moyennes de CO₂ (Mt)", f"{avg_co2:.2f}")
col3.metric("Écart-type des renouvelables", f"{std_renew:.2f}")

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.write("### Évolution des sources d’énergie")
    energy_cols = ['solar_consumption', 'wind_consumption', 'nuclear_consumption']
    energy_labels = {
        'solar_consumption': 'Solaire',
        'wind_consumption': 'Éolien',
        'nuclear_consumption': 'Nucléaire'
    }
    df_energy_by_year = df_filtered.groupby('year', as_index=False)[energy_cols].sum()
    fig_line = px.line(df_energy_by_year, x='year', y=energy_cols,
                      labels={'value': 'Consommation (TWh)', 'year': 'Année', 'variable': 'Source d’énergie'},
                      title="Consommation d’énergie par source")
    fig_line.for_each_trace(lambda trace: trace.update(name=energy_labels.get(trace.name, trace.name)))
    st.plotly_chart(fig_line, width='stretch')

with col_right:
    st.write("### Répartition des émissions de CO₂")
    df_co2_hist = df_filtered.dropna(subset=['greenhouse_gas_emissions'])
    if not df_co2_hist.empty:
        fig_hist = px.histogram(
            df_co2_hist,
            x='greenhouse_gas_emissions',
            nbins=30,
            labels={'greenhouse_gas_emissions': 'Émissions de CO₂ (Mt)', 'count': 'Nombre de relevés'},
            title=f"Distribution des émissions — {selected_country}"
        )
        st.plotly_chart(fig_hist, width='stretch')
    else:
        st.warning("Données insuffisantes pour afficher l’histogramme du CO₂.")

st.write("### Relation entre PIB et consommation d’énergie")
# On supprime les lignes où les émissions de gaz à effet de serre sont manquantes pour éviter l'erreur de Plotly
df_scatter = df_filtered.dropna(subset=['greenhouse_gas_emissions'])

if not df_scatter.empty:
    fig_scatter = px.scatter(df_scatter, x='gdp', y='primary_energy_consumption', 
                             size='greenhouse_gas_emissions', color='renewables_pct',
                             hover_name='year',
                             labels={
                                 'gdp': 'PIB',
                                 'primary_energy_consumption': 'Consommation d’énergie primaire (TWh)',
                                 'greenhouse_gas_emissions': 'Émissions de GES (Mt)',
                                 'renewables_pct': 'Part des renouvelables (%)',
                                 'year': 'Année'
                             },
                             title="PIB et consommation d’énergie (taille = émissions de GES)")
    st.plotly_chart(fig_scatter, width='stretch')
else:
    st.warning("Données insuffisantes pour afficher le graphique de corrélation.")

st.write("### Répartition du statut solaire")
st.table(df_filtered['solar_status'].value_counts())

if st.checkbox("Afficher les données brutes"):
    st.dataframe(df_filtered)
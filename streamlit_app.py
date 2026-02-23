import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Analyse Énergie Mondiale", layout="wide")

@st.cache_data
def load_data():

    df = pd.read_csv("world_energy_consumption.csv")
    
    df_clean = df.dropna(subset=['iso_code'])
    
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

st.sidebar.header("Filtres d'exploration")

countries = sorted(df['country'].unique())
selected_country = st.sidebar.selectbox("Sélectionner un pays", countries, index=countries.index("France") if "France" in countries else 0)

year_range = st.sidebar.slider("Choisir la période", 
                               int(df['year'].min()), 
                               int(df['year'].max()), 
                               (1990, 2021))

df_filtered = df[(df['country'] == selected_country) & (df['year'].between(year_range[0], year_range[1]))]

st.title(f"Analyse Énergétique : {selected_country}")
st.markdown(f"Étude des données de **{year_range[0]}** à **{year_range[1]}**")

st.subheader("Indicateurs Clés (KPIs)")

total_cons = df_filtered['primary_energy_consumption'].sum()
avg_co2 = df_filtered['greenhouse_gas_emissions'].mean()
std_renew = df_filtered['renewables_consumption'].std()

col1, col2, col3 = st.columns(3)
col1.metric("Consommation Totale (TWh)", f"{total_cons:,.2f}")
col2.metric("Émissions CO2 Moyennes", f"{avg_co2:.2f} Mt")
col3.metric("Écart-type Renouvelables", f"{std_renew:.2f}")

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.write("### Évolution de la consommation")
    fig_line = px.line(df_filtered, x='year', y=['solar_consumption', 'wind_consumption', 'nuclear_consumption'],
                      labels={'value': 'TWh', 'year': 'Année'},
                      title="Solaire vs Vent vs Nucléaire")
    st.plotly_chart(fig_line, use_container_width=True)

with col_right:
    st.write("### Distribution du CO2 par pays (Année max)")
    latest_year = df_filtered['year'].max()
    df_latest = df[df['year'] == latest_year]
    fig_hist = px.histogram(df_latest, x='greenhouse_gas_emissions', nbins=50, 
                            title=f"Répartition mondiale du CO2 en {latest_year}")
    st.plotly_chart(fig_hist, use_container_width=True)

st.write("### Corrélation PIB vs Énergie")
# On supprime les lignes où les émissions de gaz à effet de serre sont manquantes pour éviter l'erreur de Plotly
df_scatter = df_filtered.dropna(subset=['greenhouse_gas_emissions'])

if not df_scatter.empty:
    fig_scatter = px.scatter(df_scatter, x='gdp', y='primary_energy_consumption', 
                             size='greenhouse_gas_emissions', color='renewables_pct',
                             hover_name='year', title="PIB vs Consommation (Taille = Émissions GES)")
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.warning("Données insuffisantes pour afficher le graphique de corrélation.")

st.write("### Statut Solaire (Répartition des relevés)")
st.table(df_filtered['solar_status'].value_counts())

if st.checkbox("Afficher les données brutes"):
    st.dataframe(df_filtered)
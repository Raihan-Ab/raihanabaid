import pandas as pd
import plotly.express as px
import streamlit as st
from st_aggrid import AgGrid
from google.oauth2.service_account import Credentials
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from io import BytesIO
import json

# Konfigurasi Streamlit
st.set_page_config(page_title="Dashboard Interaktif Piala Dunia", layout="wide")
st.title("\u26bd\ufe0f Dashboard Interaktif Piala Dunia FIFA")

# Autentikasi Google Sheets dari secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
service_account_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"])
credentials = Credentials.from_service_account_info(service_account_info, scopes=scope)
client = gspread.authorize(credentials)
sheet = client.open("WorldCups").sheet1
df = get_as_dataframe(sheet).dropna(how="all")

# Preprocessing
if 'Attendance' in df.columns:
    df['Attendance'] = df['Attendance'].astype(str).str.replace('.', '', regex=False).astype(float)
df['GoalsScored'] = pd.to_numeric(df['GoalsScored'], errors='coerce')
df['MatchesPlayed'] = pd.to_numeric(df['MatchesPlayed'], errors='coerce')
df['QualifiedTeams'] = pd.to_numeric(df['QualifiedTeams'], errors='coerce')
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')

# Sidebar filter
st.sidebar.header("\ud83d\udd0d Filter")
year_range = st.sidebar.slider("Tahun", int(df['Year'].min()), int(df['Year'].max()), (int(df['Year'].min()), int(df['Year'].max())))
countries = st.sidebar.multiselect("Negara Pemenang", df['Winner'].dropna().unique(), default=list(df['Winner'].dropna().unique()))

# Filter data
df_filtered = df[(df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1]) & (df['Winner'].isin(countries))]

# Statistik tambahan
st.sidebar.markdown("---")
st.sidebar.metric("Rata-rata Gol", f"{df_filtered['GoalsScored'].mean():.2f}")
st.sidebar.metric("Jumlah Penonton Tertinggi", f"{df_filtered['Attendance'].max():,.0f}")
st.sidebar.metric("Jumlah Pertandingan Terbanyak", f"{df_filtered['MatchesPlayed'].max():,.0f}")

# Tabel interaktif & editable
st.subheader("\u270f\ufe0f Edit Data Langsung")
edited_df = st.data_editor(df_filtered, use_container_width=True, num_rows="dynamic")

if st.button("\ud83d\udcc5 Simpan Perubahan ke Google Sheets"):
    set_with_dataframe(sheet, edited_df)
    st.success("Data berhasil diperbarui di Google Sheets!")

# Grafik
def line_chart(title, x, y, color):
    return px.line(df_filtered, x=x, y=y, markers=True, color_discrete_sequence=[color], title=title)

st.subheader("\u26bd Jumlah Gol")
st.plotly_chart(line_chart("Jumlah Gol dari Waktu ke Waktu", 'Year', 'GoalsScored', 'blue'), use_container_width=True)

st.subheader("\ud83d\uddd5 Jumlah Pertandingan")
st.plotly_chart(line_chart("Jumlah Pertandingan", 'Year', 'MatchesPlayed', 'orange'), use_container_width=True)

st.subheader("\ud83d\udc65 Jumlah Tim Lolos")
st.plotly_chart(line_chart("Jumlah Tim yang Lolos", 'Year', 'QualifiedTeams', 'green'), use_container_width=True)

st.subheader("\ud83d\udc41\ufe0f Jumlah Penonton")
st.plotly_chart(line_chart("Jumlah Penonton", 'Year', 'Attendance', 'red'), use_container_width=True)

# Frekuensi kemenangan
st.subheader("\ud83c\udfc6 Frekuensi Kemenangan Negara")
winner_counts = df_filtered['Winner'].value_counts().reset_index()
winner_counts.columns = ['Country', 'Wins']
st.plotly_chart(px.bar(winner_counts, x='Wins', y='Country', orientation='h', color='Country', title='Jumlah Kemenangan per Negara'), use_container_width=True)

# Choropleth map
st.subheader("\ud83c\udf0d Peta Negara Pemenang")
st.plotly_chart(px.choropleth(winner_counts, locations="Country", locationmode="country names",
                              color="Wins", color_continuous_scale="Viridis",
                              title="Peta Kemenangan Piala Dunia"), use_container_width=True)

# Download sebagai CSV
st.subheader("\u2b07\ufe0f Unduh Data yang Telah Difilter")
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv(df_filtered)
st.download_button("Download CSV", csv, "data_piala_dunia.csv", "text/csv", key='download-csv')

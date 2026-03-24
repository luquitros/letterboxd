import plotly.express as px
import pandas as pd
import pycountry

def get_iso3(country_name):
    """Converte nome do país para código ISO de 3 letras."""
    try:
        return pycountry.countries.lookup(country_name).alpha_3
    except:
        return None

def gerar_mapa(dados, output_path="mapa_filmes.html"):
    if isinstance(dados, dict):
        df_counts = pd.DataFrame(list(dados.items()), columns=['Country', 'Count'])
    else:
        df_counts = dados.copy()

    df_counts['Country'] = df_counts['Country'].apply(lambda x: x[0] if isinstance(x, list) else x)

    df_counts['ISO_CODE'] = df_counts['Country'].apply(get_iso3)
    
    df_counts = df_counts.dropna(subset=['ISO_CODE'])
    
    df_counts['ISO_CODE'] = df_counts['ISO_CODE'].astype(str)

    fig = px.choropleth(
        df_counts,
        locations="ISO_CODE",
        color="Count",
        hover_name="Country",
        color_continuous_scale=["#2c3440", "#00c030", "#00e054"],
        projection="natural earth",
        template="plotly_dark"
    )

    fig.update_layout(
        margin={"r":0,"t":40,"l":0,"b":0},
        paper_bgcolor="#14181c",
        plot_bgcolor="#14181c",
        geo=dict(bgcolor="#14181c", showframe=False)
    )

    fig.write_html(output_path)
    print(f"✅ Sucesso! Mapa gerado em: {output_path}")
if __name__ == "__main__":
    try:
        df_teste = pd.read_csv("cache_paises.csv") 
        gerar_mapa(df_teste)
    except Exception as e:
        print(f"Erro ao testar mapa: {e}")
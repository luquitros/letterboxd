import plotly.express as px
import pandas as pd
import pycountry

def get_iso3(country_name):
    """Converte nome do país para código ISO de 3 letras."""
    try:
        return pycountry.countries.lookup(country_name).alpha_3
    except:
        return None

def gerar_mapa(df_cache, output_path="mapa_filmes.html"):
    df_exploded = df_cache.assign(Countries=df_cache['Countries'].str.split('|')).explode('Countries')
    
    df_counts = df_exploded['Countries'].value_counts().reset_index()
    df_counts.columns = ['Country', 'Count']
    
    df_counts['ISO_CODE'] = df_counts['Country'].apply(get_iso3)
    df_counts = df_counts.dropna(subset=['ISO_CODE'])

    fig = px.choropleth(
        df_counts,
        locations="ISO_CODE",
        color="Count",
        hover_name="Country",
        color_continuous_scale=["#2c3440", "#00c030", "#00e054"],
        projection="natural earth",
        title="Minha Jornada Cinematográfica Mundial",
        template="plotly_dark"
    )

    fig.update_layout(
        margin={"r":0,"t":50,"l":0,"b":0},
        paper_bgcolor="#14181c", 
        plot_bgcolor="#14181c",
        font_color="#ffffff",
        coloraxis_showscale=True,
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular',
            bgcolor="#14181c"
        )
    )

    fig.write_html(output_path)
    print(f"✅ Mapa atualizado com sucesso em: {output_path}")

if __name__ == "__main__":
    try:
        df_teste = pd.read_csv("cache_paises.csv") 
        gerar_mapa(df_teste)
    except Exception as e:
        print(f"Erro ao testar mapa: {e}")
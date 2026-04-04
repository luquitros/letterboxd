import pandas as pd
import plotly.express as px
import pycountry

_OVERRIDES = {
    "United States of America": "USA",
    "United States": "USA",
    "South Korea": "KOR",
    "North Korea": "PRK",
    "Russia": "RUS",
    "Bolivia": "BOL",
    "Venezuela": "VEN",
    "Tanzania": "TZA",
    "Syria": "SYR",
    "Iran": "IRN",
    "Vietnam": "VNM",
    "Czech Republic": "CZE",
    "Taiwan": "TWN",
    "Kosovo": "XKX",
    "Palestine": "PSE",
    "Macau": "MAC",
    "Hong Kong": "HKG",
    "United Kingdom": "GBR",
    "Moldova": "MDA",
    "South Sudan": "SSD",
    "Ivory Coast": "CIV",
}


def get_iso3(country_name: str) -> str | None:
    """Converte nome do país para código ISO-3166-1 alpha-3."""
    if not country_name or not country_name.strip():
        return None
    if country_name in _OVERRIDES:
        return _OVERRIDES[country_name]
    try:
        return pycountry.countries.lookup(country_name).alpha_3
    except LookupError:
        pass
    try:
        results = pycountry.countries.search_fuzzy(country_name)
        if results:
            return results[0].alpha_3
    except LookupError:
        pass
    return None


def gerar_mapa(dados, output_path="mapa_filmes.html"):
    if isinstance(dados, dict):
        df_counts = pd.DataFrame(list(dados.items()), columns=["Country", "Count"])
    else:
        df_counts = dados.copy()

    df_counts["Country"] = df_counts["Country"].apply(
        lambda x: x[0] if isinstance(x, list) else x
    )

    sem_iso = [p for p in df_counts["Country"].unique() if get_iso3(p) is None]
    if sem_iso:
        print(f"\n⚠️  {len(sem_iso)} países sem código ISO (ignorados no mapa):")
        for p in sorted(sem_iso):
            print(f"   • {p}")

    df_counts["ISO_CODE"] = df_counts["Country"].apply(get_iso3)
    df_counts = df_counts.dropna(subset=["ISO_CODE"])
    df_counts["ISO_CODE"] = df_counts["ISO_CODE"].astype(str)

    print("\nTop 10 países:")
    print(df_counts.nlargest(10, "Count")[["Country", "Count"]].to_string(index=False))

    fig = px.choropleth(
        df_counts,
        locations="ISO_CODE",
        locationmode="ISO-3",
        color="Count",
        hover_name="Country",
        color_continuous_scale=["#2c3440", "#00c030", "#00e054"],
        projection="natural earth",
        template="plotly_dark",
        title=" Filmes por País de Produção",
        labels={"Count": "Filmes assistidos"},
    )

    fig.update_layout(
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        paper_bgcolor="#14181c",
        plot_bgcolor="#14181c",
        geo=dict(bgcolor="#14181c", showframe=False, showcoastlines=True),
    )

    fig.write_html(output_path)
    print(f"✅ Mapa salvo em: {output_path}")


if __name__ == "__main__":
    try:
        df_teste = pd.read_csv("tmdb_cache.csv")
        gerar_mapa(df_teste)
    except Exception as e:
        print(f"Erro ao testar mapa: {e}")
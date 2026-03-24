import pycountry
import pandas as pd
import plotly.express as px



_OVERRIDES: dict[str, str] = {
    "United States of America": "USA",
    "United States":            "USA",
    "South Korea":              "KOR",
    "North Korea":              "PRK",
    "Russia":                   "RUS",
    "Bolivia":                  "BOL",
    "Venezuela":                "VEN",
    "Tanzania":                 "TZA",
    "Syria":                    "SYR",
    "Iran":                     "IRN",
    "Vietnam":                  "VNM",
    "Czech Republic":           "CZE",
    "Taiwan":                   "TWN",
    "Kosovo":                   "XKX",
    "Palestine":                "PSE",
    "Macau":                    "MAC",
    "Hong Kong":                "HKG",
}


def _nome_para_iso3(nome: str) -> str | None:
    """Converte nome de país (TMDB) para código ISO-3166-1 alpha-3."""
    if nome in _OVERRIDES:
        return _OVERRIDES[nome]
    
    pais = pycountry.countries.get(name=nome)
    if pais:
        return pais.alpha_3
    
    try:
        resultados = pycountry.countries.search_fuzzy(nome)
        if resultados:
            return resultados[0].alpha_3
    except LookupError:
        pass
    return None


def _iso3_para_nome_display(iso3: str) -> str:
    """Retorna o nome comum do país a partir do código ISO-3."""
    pais = pycountry.countries.get(alpha_3=iso3)
    return pais.name if pais else iso3


def gerar_mapa(
    todos_paises_raw: list[str],
    filmes_por_pais_raw: dict[str, list[str]],
    output_html: str,
) -> None:
    """
    Gera mapa coroplético com tooltips mostrando os filmes de cada país.

    Parâmetros
    ----------
    todos_paises_raw    : lista de nomes de países (com repetições)
    filmes_por_pais_raw : dict {nome_pais -> [titulo, ...]} para o tooltip
    output_html         : caminho do arquivo HTML de saída
    """
    
    paises_iso = []
    sem_iso: set[str] = set()

    for nome in todos_paises_raw:
        iso = _nome_para_iso3(nome)
        if iso:
            paises_iso.append(iso)
        else:
            sem_iso.add(nome)

    if sem_iso:
        print(f"\n⚠️  {len(sem_iso)} país(es) sem código ISO (serão ignorados no mapa):")
        for p in sorted(sem_iso):
            print(f"   • {p}")

    
    serie = pd.Series(paises_iso)
    contagem = serie.value_counts().reset_index()
    contagem.columns = ["ISO3", "Filmes"]
    contagem["País"] = contagem["ISO3"].apply(_iso3_para_nome_display)

    
    def _tooltip(iso3: str) -> str:
        nome_raw_list = [
            nome for nome, i in
            ((n, _nome_para_iso3(n)) for n in filmes_por_pais_raw)
            if i == iso3
        ]
        titulos: list[str] = []
        for nome_raw in nome_raw_list:
            titulos.extend(filmes_por_pais_raw.get(nome_raw, []))
        titulos = sorted(set(titulos))
        sample = titulos[:10]
        extra = len(titulos) - len(sample)
        texto = "<br>".join(f"• {t}" for t in sample)
        if extra:
            texto += f"<br><i>...e mais {extra}</i>"
        return texto

    contagem["Títulos"] = contagem["ISO3"].apply(_tooltip)

    
    print("\nTop 10 países:")
    print(contagem[["País", "Filmes"]].head(10).to_string(index=False))

    
    fig = px.choropleth(
        contagem,
        locations="ISO3",
        locationmode="ISO-3",
        color="Filmes",
        color_continuous_scale="Viridis",
        hover_name="País",
        hover_data={"ISO3": False, "Filmes": True, "Títulos": True},
        title="🎬 Meu Cinema Mundial — Filmes por País de Produção",
        labels={"Filmes": "Filmes assistidos", "Títulos": "Filmes"},
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Filmes: %{z}<br>"
            "%{customdata[1]}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        coloraxis_colorbar=dict(title="Filmes"),
        margin=dict(l=0, r=0, t=50, b=0),
    )

    fig.write_html(output_html)
    print(f"\n✅ Mapa salvo em '{output_html}' — abra no navegador!")
    fig.show()
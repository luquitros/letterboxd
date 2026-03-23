import pandas as pd
import plotly.express as px


def gerar_mapa(todos_paises, output_html):
    """Recebe lista de países e gera mapa coroplético HTML."""
    serie = pd.Series(todos_paises)
    contagem = serie.value_counts().reset_index()
    contagem.columns = ["País", "Filmes"]

    print("\nTop 10 países:")
    print(contagem.head(10).to_string(index=False))

    fig = px.choropleth(
        contagem,
        locations="País",
        locationmode="country names",
        color="Filmes",
        color_continuous_scale="Viridis",
        title="🎬 Meu Cinema Mundial — Filmes por País de Produção",
        labels={"Filmes": "Filmes assistidos"}
    )

    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        coloraxis_colorbar=dict(title="Filmes"),
        margin=dict(l=0, r=0, t=50, b=0)
    )

    fig.write_html(output_html)
    print(f"\n Mapa salvo em '{output_html}' — abra no navegador!")
    fig.show()
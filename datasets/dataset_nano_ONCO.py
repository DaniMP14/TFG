import pandas as pd

# VERSIÓN SOLO SEGUNDA REDUCCIÓN (ONCO)

# Cargar el dataset reducido (204 filas)
df = pd.read_excel("dataset_NANO.xlsx")

# Lista de términos oncológicos relevantes
oncology_keywords = [
    "oncology", "antineoplastic", "cancer", "tumor", "carcinoma", "chemotherapy",
    "pharmacologic substance", "therapeutic agent", "drug", "cytotoxic", "apoptosis"
]

pattern = "|".join(oncology_keywords)

# Filtrar filas donde los términos aparecen en 'Synonyms', 'Definition', 'Display Name' o 'Semantic Type'
mask = (
    df["Synonyms"].str.contains(pattern, case=False, na=False) |
    df["Definition"].str.contains(pattern, case=False, na=False) |
    df["Display Name"].str.contains(pattern, case=False, na=False) |
    df["Semantic Type"].str.contains(pattern, case=False, na=False)
)

df_onco = df[mask]

df_onco.to_csv("dataset_nano_ONCO.csv", index=False)
df_onco.to_parquet("dataset_nano_ONCO.parquet", index=False)

print(f"Filas seleccionadas: {df_onco.shape[0]}")
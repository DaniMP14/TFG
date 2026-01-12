import pandas as pd


# VERSIÓN FINAL - INCLUYE LA SEGUNDA REDUCCIÓN (ONCO)

# Cargamos todo el dataset original
df = pd.read_excel("Tesauro.xlsx")

# Lista de términos relevantes para la primera reducción (nanotecnología)
keywords = [
    "nanoparticle", "nanomaterial", "nanostructure", "nanocomposite", "nanoscale", 
    "nanotechnology", "nanomedicine", "nanocarrier", "nanosensor", "nanotube"
]

pattern = "|".join(keywords)

# Filtrar filas donde los términos aparecen en 'Synonyms', 'Display Name' o 'Definition'
mask = (
    df["Synonyms"].str.contains(pattern, case=False, na=False) |
    df["Display Name"].str.contains(pattern, case=False, na=False) |
    df["Definition"].str.contains(pattern, case=False, na=False)
)

df_reducido = df[mask]

df_reducido.to_parquet("dataset_NANO.parquet", index=False)
df_reducido.to_csv("dataset_NANO.csv", index=False)

print(f"Filas seleccionadas: {df_reducido.shape[0]}")

# Cargar el dataset reducido (204 filas)
df2 = pd.read_csv("dataset_NANO.csv")

# Lista de términos oncológicos relevantes
oncology_keywords = [
    "oncology", "antineoplastic", "cancer", "tumor", "carcinoma", "chemotherapy",
    "pharmacologic substance", "therapeutic agent", "drug", "cytotoxic", "apoptosis"
]

# Eliminar 'pharmacologic substance' y 'therapeutic agent' para evitar demasiados términos no relevantes
# No se elimina directamente ya que en el proceso de creación de la ontología si se usan algunos de los términos

pattern2 = "|".join(oncology_keywords)

# Filtrar filas donde los términos aparecen en 'Synonyms', 'Definition', 'Display Name' o 'Semantic Type'
mask2 = (
    df2["Synonyms"].str.contains(pattern2, case=False, na=False) |
    df2["Definition"].str.contains(pattern2, case=False, na=False) |
    df2["Display Name"].str.contains(pattern2, case=False, na=False) |
    df2["Semantic Type"].str.contains(pattern2, case=False, na=False)
)

df_onco = df2[mask2]

df_onco.to_csv("dataset_FINAL.csv", index=False)
df_onco.to_excel("dataset_FINAL.xlsx", index=False)

print(f"Filas seleccionadas: {df_onco.shape[0]}")

# tercera reducción manual para eliminar términos no relevantes
df3 = pd.read_csv("dataset_FINAL.csv")

rows_to_remove = list(range(56, 64)) + list(range(68, 70)) + [81] + list(range(89, 93)) + list(range(96, 98)) + [99, 101, 105, 140]
df3 = df3.drop(rows_to_remove)

df3.to_csv("dataset_FINAL2.csv", index=False)
df3.to_excel("dataset_FINAL2.xlsx", index=False)
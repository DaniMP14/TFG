import pandas as pd
import getpass
import mysql.connector

# Leer el CSV
df = pd.read_csv("../datasets/tesauro_filtrado.csv")

# Conectarse a MySQL
# contraseña solicitada de forma segura
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password = getpass.getpass("Introduce la contraseña de MySQL: "),
    database="tfg_nanotech",
    charset='utf8mb4'
)

cursor = conn.cursor()

# Crear la tabla (columnas de texto grandes como TEXT)
cursor.execute("""
CREATE TABLE IF NOT EXISTS thesaurus_concepts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50),
    display_name VARCHAR(255),
    definition TEXT,
    synonyms TEXT,
    parents TEXT,
    concept_subset TEXT
)
""")

# Si la tabla existía con columnas más pequeñas, intentar convertirlas a MEDIUMTEXT
try:
    cursor.execute("ALTER TABLE thesaurus_concepts MODIFY COLUMN parents MEDIUMTEXT")
    cursor.execute("ALTER TABLE thesaurus_concepts MODIFY COLUMN concept_subset MEDIUMTEXT")
except mysql.connector.Error:
    # Ignorar errores (por ejemplo, si la tabla no existía o las columnas ya son suficientemente grandes)
    pass


# Si no importa perder los datos anteriores (si los hay), los borramos para no duplicar
cursor.execute("TRUNCATE TABLE thesaurus_concepts")

# Insertar los datos
for _, row in df.iterrows():
    # Normalizar valores None a cadenas vacías para evitar problemas con INSERT
    code = '' if pd.isna(row.get('Code')) else str(row.get('Code'))
    display_name = '' if pd.isna(row.get('Display Name')) else str(row.get('Display Name'))
    definition = '' if pd.isna(row.get('Definition')) else str(row.get('Definition'))
    synonyms = '' if pd.isna(row.get('Synonyms')) else str(row.get('Synonyms'))
    parents = '' if pd.isna(row.get('Parents')) else str(row.get('Parents'))
    concept_subset = '' if pd.isna(row.get('Concept in Subset')) else str(row.get('Concept in Subset'))

    cursor.execute("""
        INSERT INTO thesaurus_concepts 
        (code, display_name, definition, synonyms, parents, concept_subset)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        code,
        display_name,
        definition,
        synonyms,
        parents,
        concept_subset
    ))

conn.commit()
cursor.close()
conn.close()
print("Datos importados correctamente")

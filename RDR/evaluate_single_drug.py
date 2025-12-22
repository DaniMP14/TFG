"""
Script para evaluar un único fármaco en producción.

Simula el flujo real: entrada de datos → extracción → RDR → recomendación.

Sirve para:
- Evaluar fármacos del dataset GENERAL NCIt por código o nombre
- Evaluar textos libres como fármacos (inputs sintéticos)
"""
import json
import sys
import re
from pathlib import Path

"""
Evalúa un fármaco desde el dataset NCIt (el general) usando código o nombre.
Aclaración: el general tiene conceptos más amplios y menos detallados que el especializado.
Todas las filas no tienen por qué tener Display Name, puede estar vacía ya que no se ha tratado.

Si no se encuentra el fármaco, se intenta evaluar como texto libre.

Args:
    ncit_code: código NCIt (ej: "C123456")
    display_name: nombre del fármaco (ej: "Doxorubicin Hydrochloride Liposome")
"""
def evaluate_drug_from_ncit(ncit_code: str = None, display_name: str = None):

    import pandas as pd
    from extract_input import row_to_input
    from generate_recommendations import generate_single_drug_report
    
    # Cargar dataset
    dataset_path = Path(__file__).parent.parent / "datasets" / "Tesauro.xlsx"
    df = pd.read_excel(dataset_path, engine='openpyxl')
    
    # Buscar fármaco
    if ncit_code:
        row = df[df['Code'] == ncit_code]
    elif display_name:
        row = df[df['Display Name'].str.contains(display_name, case=False, na=False)]
    else:
        print("Error: Proporciona ncit_code o display_name")
        return
    
    if row.empty:
        if ncit_code:
            print(f"Fármaco no encontrado en el dataset con código: {ncit_code}")
            return
        
        if display_name:
            print(f"'{display_name}' no encontrado en el dataset.")
            print(f"Intentando analizar como texto libre...")
            evaluate_custom_text(display_name)
            return

    if len(row) > 1:
        print(f"Múltiples coincidencias encontradas ({len(row)}). Usando la primera.") # por ejemplo, C1000 y C10001, si escribes "C1000"
    
    # Extraer input
    drug_input = row_to_input(row.iloc[0])
    
    # Generar reporte
    report = generate_single_drug_report(drug_input)
    print(report)
    
    return drug_input


def evaluate_custom_text(text: str):
    """
    Evalúa un texto libre como si fuera un fármaco, generando un input sintético.
    """
    import pandas as pd
    from extract_input import row_to_input
    from generate_recommendations import generate_single_drug_report
    
    # Crear fila sintética para el extractor
    # Usamos el texto como Display Name y Definition para maximizar la inferencia de keywords
    fake_row = pd.Series({
        "Display Name": text,
        "Synonyms": "",
        "Definition": text, 
        "Concept in Subset": "",
        "Code": "CUSTOM_INPUT",
        "Semantic Type": "Pharmacologic Substance"
    })
    
    print(f"   Generando input sintético para: {text}")
    drug_input = row_to_input(fake_row)
    
    # Generar reporte
    report = generate_single_drug_report(drug_input)
    print(report)
    
    return drug_input


def evaluate_drug_from_json(json_path: str):
    """
    Evalúa un fármaco desde un archivo JSON de entrada.
    
    Útil para casos personalizados o datos externos al NCIt.
    """
    from generate_recommendations import generate_single_drug_report
    
    with open(json_path, 'r', encoding='utf-8') as f:
        drug_input = json.load(f)
    
    report = generate_single_drug_report(drug_input)
    print(report)
    
    return drug_input


def main():
    """Ejemplos de uso en producción."""
    
    if len(sys.argv) > 1:
        # Modo: python evaluate_single_drug.py <query>
        query = sys.argv[1]
        
        # Detectar si es código NCIt (C + números)
        if re.match(r'^C\d+$', query, re.IGNORECASE):
            print(f"Buscando por código: {query}")
            evaluate_drug_from_ncit(ncit_code=query)
        else:
            print(f"Buscando por nombre: {query}")
            evaluate_drug_from_ncit(display_name=query)
    else:
        # Modo demo: evaluar casos de ejemplo
        print("\n" + "=" * 80)
        print("MODO DEMO - Evaluando casos de ejemplo")
        print("=" * 80 + "\n")
        
        # Ejemplo 1: liposoma (debería ser lipid-based, moderate affinity, fluid)
        print("\n[EJEMPLO 1] Liposoma PEGylado\n")
        evaluate_drug_from_ncit(display_name="liposome")
        
        input("\n[Presiona Enter para siguiente ejemplo...]\n")
        
        # Ejemplo 2: nanopartícula metálica (debería ser metallic, high affinity, ordered)
        print("\n[EJEMPLO 2] Nanopartícula de oro\n")
        evaluate_drug_from_ncit(display_name="gold")
        
        input("\n[Presiona Enter para siguiente ejemplo...]\n")
        
        # Ejemplo 3: polímero (debería ser polymeric, moderate affinity, stable)
        print("\n[EJEMPLO 3] Nanopartícula polimérica\n")
        evaluate_drug_from_ncit(display_name="polymeric")


if __name__ == '__main__':
    main()

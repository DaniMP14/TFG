"""
Script para evaluar un único fármaco en producción.

Simula el flujo real: entrada de datos → extracción → RDR → recomendación.

Uso:
    python RDR/evaluate_single_drug.py
"""
import json
import sys


def evaluate_drug_from_ncit(ncit_code: str = None, display_name: str = None):
    """
    Evalúa un fármaco desde el dataset NCIt usando código o nombre.
    
    Args:
        ncit_code: código NCIt (ej: "C123456")
        display_name: nombre del fármaco (ej: "Doxorubicin Hydrochloride Liposome")
    """
    import pandas as pd
    from extract_input import row_to_input
    from generate_recommendations import generate_single_drug_report
    
    # Cargar dataset
    df = pd.read_csv("../datasets/dataset_FINAL2.csv", encoding='utf-8')
    
    # Buscar fármaco
    if ncit_code:
        row = df[df['Code'] == ncit_code]
    elif display_name:
        row = df[df['Display Name'].str.contains(display_name, case=False, na=False)]
    else:
        print("Error: Proporciona ncit_code o display_name")
        return
    
    if row.empty:
        print(f"❌ Fármaco no encontrado en el dataset")
        print(f"   Código buscado: {ncit_code}")
        print(f"   Nombre buscado: {display_name}")
        return
    
    if len(row) > 1:
        print(f"⚠ Múltiples coincidencias encontradas ({len(row)}). Usando la primera.")
    
    # Extraer input
    drug_input = row_to_input(row.iloc[0])
    
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
        # Modo: python evaluate_single_drug.py <código_ncit>
        ncit_code = sys.argv[1]
        evaluate_drug_from_ncit(ncit_code=ncit_code)
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

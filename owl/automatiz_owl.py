import pandas as pd
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef
import re

# Automatización de la ontología OWL (anotaciones) a partir de la jerarquía de clases y el dataset filtrado
# El dataset en cuestión es tesauro_filtrado, que contiene los términos de dataset_FINAL y todos los padres necesarios en la jerarquía

def clean_text(text):
    # Limpia el texto removiendo espacios extra y caracteres problemáticos
    if pd.isna(text):
        return None
    return re.sub(r'\s+', ' ', str(text)).strip()

def load_dataset(file_path):
    # Carga el dataset desde diferentes formatos
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        return pd.read_excel(file_path)
    else:
        raise ValueError("Formato de archivo no soportado. Usa CSV o Excel.")

def complete_ontology(ontology_path, dataset_path, output_path):
    # Cargar ontología
    g = Graph()
    g.parse(ontology_path, format="xml")
    
    # Definir namespaces
    BASE_NS = "http://www.semanticweb.org/daniel/ontologies/2025/9/ontologia_tfg#"
    ns = Namespace(BASE_NS)
    
    # Propiedades de anotación
    definition_prop = ns.definition
    name_prop = ns.name
    synonym_prop = ns.synonym
    semantic_type_prop = ns.semanticType
    code_prop = ns.code
    concept_prop = ns.conceptInSubset
    
    # Cargar dataset
    df = load_dataset(dataset_path)
    
    # Contadores para estadísticas
    processed = 0
    not_found = 0
    errors = 0
    
    for index, row in df.iterrows():
        try:
            code = clean_text(row['Code'])
            if not code:
                continue
                
            class_uri = URIRef(BASE_NS + code)
            
            # Verificar si la clase existe
            if (class_uri, RDF.type, OWL.Class) in g:
                
                # Añadir código como anotación
                g.add((class_uri, code_prop, Literal(code)))

                # Definición
                definition = clean_text(row.get('Definition'))
                if definition:
                    g.add((class_uri, definition_prop, Literal(definition)))
                
                # Nombre
                display_name = clean_text(row.get('Display Name'))
                synonyms_text = clean_text(row.get('Synonyms'))
                
                name = None
                if display_name:
                    name = display_name
                elif synonyms_text:
                    name = synonyms_text.split('|')[0]
                
                # Se añade como label y como name
                if name:
                    g.add((class_uri, name_prop, Literal(name)))
                    g.add((class_uri, RDFS.label, Literal(name)))
                
                # Sinónimos: segun la ontologia del Tesauro completo, se incluye también el que se usa como nombre
                if synonyms_text:
                    all_synonyms = [s.strip() for s in synonyms_text.split('|') if s.strip()]
                    for syn in all_synonyms:
                        g.add((class_uri, synonym_prop, Literal(syn)))
                
                # Tipo(s) semántico(s): una anotación por cada tipo
                semantic_type = clean_text(row.get('Semantic Type'))
                if semantic_type:
                    all_syn_types = [st.strip() for st in semantic_type.split('|') if st.strip()]
                    for st in all_syn_types:
                        g.add((class_uri, semantic_type_prop, Literal(st)))
                
                # Concept in Subset: una anotación por cada subset
                subset = clean_text(row.get('Concept in Subset'))
                if subset:
                    all_subsets = [s.strip() for s in subset.split('|') if s.strip()]
                    for s in all_subsets:
                        g.add((class_uri, concept_prop, Literal(s)))

                processed += 1
            else:
                print(f"Advertencia: Clase {code} no encontrada en la ontología")
                not_found += 1
                
        except Exception as e:
            print(f"Error procesando fila {index}: {e}")
            errors += 1
    
    # Guardar ontología actualizada
    g.serialize(destination=output_path, format="xml")
    
    print(f"\n--- Resumen ---")
    print(f"Clases procesadas: {processed}")
    print(f"Clases no encontradas: {not_found}")
    print(f"Errores: {errors}")
    print(f"Ontología guardada en: {output_path}")

# Uso
complete_ontology(
    ontology_path="version3.rdf",
    dataset_path="../datasets/tesauro_filtrado.csv",
    output_path="version3_final.rdf"
)
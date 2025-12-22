"""Runner simple que aplica las reglas GRDR a un JSONL de inputs.

Lee cada línea JSON del fichero de entrada, aplica `rule_base.evaluate` y escribe un JSONL
de salida con la predicción y la información de contexto.

Uso:
    python RDR\run_rules.py  # usa paths por defecto
"""
import json
import sys
from typing import Any, Dict

from implementacion_rdr import rule_root


def load_jsonl(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def default_empty_result():
    return {
        "rule": None,
        "output": None,
        "prediction_confidence": 0.0,
        "input_confidence": 0.0,
        "provenance": [],
        "execution_time": None,
    }


def run(input_path: str, output_path: str, n: int = 10, use_all: bool = False):
    inputs = list(load_jsonl(input_path))
    if n is not None:
        inputs = inputs[:n]

    results = []
    with open(output_path, 'w', encoding='utf-8') as out_f:
        for idx, inp in enumerate(inputs, start=1):
            # por defecto usamos SCRDR: la evaluación devuelve la primera conclusión válida
            if use_all:
                res_list = rule_root.evaluate_all(inp)
                if not res_list:
                    prediction = default_empty_result()
                else:
                    # cuando hay múltiples resultados, los incluimos como lista
                    prediction = {"multi": True, "results": res_list}
            else:
                res = rule_root.evaluate(inp)
                prediction = res if res is not None else default_empty_result()

            record = {
                "index": idx,
                "context": inp.get('context', {}),
                "prediction": prediction,
            }
            out_f.write(json.dumps(record, ensure_ascii=False) + '\n')
            results.append(record)

    return results


def main():
    input_path = r"ins/rdr_inputs_v4.jsonl"
    output_path = r"rdr_predictions_v4.jsonl"
    n = 128
    use_all = True # si True, usa evaluate_all en lugar de evaluate, obteniendo todas las conclusiones posibles
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    if len(sys.argv) > 3:
        try:
            n = int(sys.argv[3])
        except Exception:
            pass
    if len(sys.argv) > 4 and sys.argv[4] == '--all':
        use_all = True

    results = run(input_path, output_path, n=n, use_all=use_all)
    print(f"✓ Procesadas {len(results)} entradas. Predicciones guardadas en: {output_path}")
    
    # Generar reporte legible automáticamente
    try:
        from generate_recommendations import generate_batch_report
        report_path = output_path.replace('_predictions_', '_reporte_').replace('.jsonl', '.txt')
        print(f"\nGenerando reporte de decisiones...")
        generate_batch_report(output_path, report_path)
    except Exception as e:
        print(f"⚠ No se pudo generar reporte automático: {e}")
        print(f"  Ejecuta manualmente: python RDR/generate_recommendations.py")


if __name__ == '__main__':
    main()

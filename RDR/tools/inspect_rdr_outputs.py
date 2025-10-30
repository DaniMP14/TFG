"""
Utilidad para inspeccionar archivos JSONL generados por el extractor de inputs RDR.

Ejemplos de uso:
  python RDR/tools/inspect_rdr_outputs.py --file RDR/rdr_inputs_v1.jsonl --head 20
  python RDR/tools/inspect_rdr_outputs.py -f RDR/rdr_inputs_v1.jsonl --filter-surface-charge positive --save out.csv

Muestra una tabla compacta con columnas útiles y admite filtrado simple y exportación a CSV.
"""
import argparse
import json
from typing import List
import pandas as pd

DEFAULT_COLS = [
    'context.source_code', 'context.display_name', 'context.semantic_type',
    'nanoparticle.type', 'nanoparticle.type_confidence', 'nanoparticle.type_provenance',
    'nanoparticle.surface_charge', 'nanoparticle.surface_charge_confidence', 'nanoparticle.surface_charge_provenance',
    'ligand.type', 'ligand.type_confidence', 'ligand.type_provenance', 
    'ligand.charge', 'ligand.charge_confidence', 'ligand.charge_provenance',
    'ligand.polarity', 'ligand.polarity_confidence', 'ligand.polarity_provenance',
    'biomolecule.type', 'biomolecule.type_confidence', 'biomolecule.type_provenance',
    'surface.material', 'surface.material_confidence', 'surface.material_provenance',
    'surface.charge', 'surface.charge_confidence', 'surface.charge_provenance',
]


def load_jsonl(path: str) -> List[dict]:
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                # skip malformed
                continue
    return data


def flatten(record: dict, prefix: str = '') -> dict:
    out = {}
    for k, v in record.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                out[f"{k}.{kk}"] = vv
        else:
            out[k] = v
    return out


def build_df(records: List[dict]) -> pd.DataFrame:
    flat = [flatten(r) for r in records]
    df = pd.DataFrame(flat)
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--file', '-f', required=True, help='Path to JSONL file')
    p.add_argument('--head', '-n', type=int, default=20, help='Show first N rows')
    p.add_argument('--cols', '-c', nargs='+', help='Columns to show (dot notation)')
    p.add_argument('--filter-surface-charge', choices=['positive','negative','neutral','unknown','ambiguous'], help='Filter by nanoparticle.surface_charge')
    p.add_argument('--save', '-s', help='Save resulting table to CSV')
    args = p.parse_args()

    records = load_jsonl(args.file)
    if not records:
        print('No records found in', args.file)
        return

    df = build_df(records)
    cols = args.cols if args.cols else DEFAULT_COLS
    # keep only available columns
    cols = [c for c in cols if c in df.columns]
    if not cols:
        print('No requested columns present in data. Available columns:')
        print(', '.join(df.columns.tolist()))
        return

    out = df[cols].copy()
    if args.filter_surface_charge:
        col = 'nanoparticle.surface_charge'
        if col in out.columns:
            out = out[out[col] == args.filter_surface_charge]
        else:
            print(f'No column {col} to filter on')

    # show head
    pd.set_option('display.max_colwidth', 120)
    print(out.head(args.head).to_string(index=False))

    if args.save:
        out.to_csv(args.save, index=False)
        print('Saved', args.save)


if __name__ == '__main__':
    main()

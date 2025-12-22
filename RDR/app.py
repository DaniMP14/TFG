import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os
import json
from pathlib import Path
import pandas as pd
import threading

# Add current directory to sys.path to ensure imports work
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from extract_input import row_to_input
    from generate_recommendations import generate_single_drug_report
except ImportError as e:
    # Fallback for when running from root
    try:
        sys.path.append(str(current_dir / "RDR"))
        from RDR.extract_input import row_to_input
        from RDR.generate_recommendations import generate_single_drug_report
    except ImportError:
        pass

class RDRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RDR Drug Evaluator")
        self.root.geometry("900x700")
        
        self.df = None
        # Path to dataset relative to this script
        self.dataset_path = Path(__file__).parent.parent / "datasets" / "Tesauro.xlsx"
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header_lbl = ttk.Label(main_frame, text="RDR Drug Evaluation System", font=("Segoe UI", 16, "bold"))
        header_lbl.pack(pady=(0, 10))
        
        # Tabs
        tab_control = ttk.Notebook(main_frame)
        
        self.tab_ncit = ttk.Frame(tab_control)
        self.tab_custom = ttk.Frame(tab_control)
        self.tab_full = ttk.Frame(tab_control)
        
        tab_control.add(self.tab_ncit, text='  NCIt Search  ')
        tab_control.add(self.tab_custom, text='  Custom Input  ')
        tab_control.add(self.tab_full, text='  Full Dataset Report  ')
        tab_control.pack(expand=False, fill="x")
        
        # --- NCIt Tab ---
        frame_ncit = ttk.Frame(self.tab_ncit, padding="15")
        frame_ncit.pack(fill="x")
        
        lbl_search = ttk.Label(frame_ncit, text="Search by NCIt Code (e.g., C12345) or Drug Name:")
        lbl_search.pack(fill='x', pady=(0, 5))
        
        search_container = ttk.Frame(frame_ncit)
        search_container.pack(fill='x')
        
        self.entry_search = ttk.Entry(search_container, font=("Segoe UI", 10))
        self.entry_search.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.entry_search.bind('<Return>', lambda e: self.run_ncit_search())
        
        btn_search = ttk.Button(search_container, text="Analyze", command=self.run_ncit_search)
        btn_search.pack(side='right')
        
        lbl_hint = ttk.Label(frame_ncit, text="* Loads data from datasets/Tesauro.xlsx", font=("Segoe UI", 8), foreground="gray")
        lbl_hint.pack(fill='x', pady=(5, 0))
        
        # --- Custom Tab ---
        frame_custom = ttk.Frame(self.tab_custom, padding="15")
        frame_custom.pack(fill="both", expand=True)
        
        lbl_name = ttk.Label(frame_custom, text="Drug Name:")
        lbl_name.pack(fill='x', pady=(0, 5))
        
        self.entry_name = ttk.Entry(frame_custom, font=("Segoe UI", 10))
        self.entry_name.pack(fill='x', pady=(0, 10))
        
        lbl_desc = ttk.Label(frame_custom, text="Description (include keywords like 'liposome', 'gold', 'positive charge', etc.):")
        lbl_desc.pack(fill='x', pady=(0, 5))
        
        self.text_desc = tk.Text(frame_custom, height=4, font=("Segoe UI", 10))
        self.text_desc.pack(fill='x', pady=(0, 10))
        
        btn_custom = ttk.Button(frame_custom, text="Analyze Custom Input", command=self.run_custom_analysis)
        btn_custom.pack(anchor='e')

        # --- Full Dataset Tab ---
        frame_full = ttk.Frame(self.tab_full, padding="15")
        frame_full.pack(fill="both", expand=True)
        
        lbl_full = ttk.Label(frame_full, text="Generate Full Report (dataset_FINAL2.csv)", font=("Segoe UI", 12))
        lbl_full.pack(pady=(0, 10))
        
        desc_full = ttk.Label(frame_full, text="This will evaluate all entries in the dataset and generate a JSON report similar to rdr_reporte_v4.json.\nThis process may take a moment.", wraplength=600)
        desc_full.pack(pady=(0, 20))
        
        btn_full = ttk.Button(frame_full, text="Run Full Evaluation", command=self.start_full_evaluation_thread)
        btn_full.pack()
        
        # --- Output Area ---
        frame_output = ttk.LabelFrame(main_frame, text="Analysis Report", padding="10")
        frame_output.pack(fill="both", expand=True, pady=(10, 0))
        
        self.text_output = scrolledtext.ScrolledText(frame_output, state='disabled', font=("Consolas", 10))
        self.text_output.pack(fill="both", expand=True)

    def start_full_evaluation_thread(self):
        threading.Thread(target=self.run_full_evaluation, daemon=True).start()

    def run_full_evaluation(self):
        try:
            self.log("Starting full evaluation... Loading dataset_FINAL2.csv...")
            
            # Load specific dataset for this task
            csv_path = Path(__file__).parent.parent / "datasets" / "dataset_FINAL2.csv"
            if not csv_path.exists():
                self.log(f"Error: {csv_path} not found.")
                return
                
            df_full = pd.read_csv(csv_path, encoding='utf-8')
            
            self.log(f"Loaded {len(df_full)} records. Processing rules...")
            
            # Lazy import to ensure availability
            try:
                from implementacion_rdr import rule_root
                from generate_recommendations import generate_recommendation
            except ImportError:
                # Try adjusting path if needed, though app.py setup should handle it
                sys.path.append(str(Path(__file__).parent))
                from implementacion_rdr import rule_root
                from generate_recommendations import generate_recommendation

            reports = []
            stats = {
                "aprobados": 0,
                "condicionales": 0,
                "rechazados": 0,
                "requieren_validacion": 0
            }
            
            total = len(df_full)
            for idx, row in df_full.iterrows():
                if idx % 50 == 0:
                    self.log(f"Processing... {idx}/{total}")
                
                # Extract
                drug_input = row_to_input(row)
                
                # Evaluate
                prediction = rule_root.evaluate(drug_input)
                if prediction is None:
                    prediction = {
                        "rule": "No rule matched",
                        "predicted_affinity": "unknown",
                        "monolayer_order": "unknown",
                        "rule_confidence": 0.0
                    }
                
                # Recommend
                context = drug_input.get("context", {})
                rec = generate_recommendation(prediction, context)
                
                # Update stats
                decision = rec.get("decision_produccion", "")
                if "APROBADO" in decision:
                    stats["aprobados"] += 1
                elif "VIABLE" in decision:
                    stats["condicionales"] += 1
                elif "RECHAZADO" in decision:
                    stats["rechazados"] += 1
                else:
                    stats["requieren_validacion"] += 1
                
                reports.append(rec)
            
            final_json = {
                "estadisticas": stats,
                "reportes": reports
            }
            
            json_str = json.dumps(final_json, indent=2, ensure_ascii=False)
            self.log(json_str)
            
        except Exception as e:
            self.log(f"Error in full evaluation: {e}")
            import traceback
            print(traceback.format_exc())

    def log(self, message):
        self.text_output.config(state='normal')
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(tk.END, message)
        self.text_output.config(state='disabled')

    def load_dataset(self):
        if self.df is not None:
            return True
            
        try:
            self.log("Loading dataset... Please wait (this may take a few seconds)...")
            self.root.update()
            
            if not self.dataset_path.exists():
                self.log(f"Error: Dataset not found at {self.dataset_path}")
                return False
                
            # Check extension to decide loader
            if self.dataset_path.suffix == '.csv':
                self.df = pd.read_csv(self.dataset_path, encoding='utf-8')
            else:
                self.df = pd.read_excel(self.dataset_path, engine='openpyxl')
            return True
        except Exception as e:
            self.log(f"Error loading dataset: {e}")
            return False

    def run_ncit_search(self):
        query = self.entry_search.get().strip()
        if not query:
            messagebox.showwarning("Input Error", "Please enter a search term.")
            return
            
        if not self.load_dataset():
            return
            
        try:
            # Search logic
            if query.upper().startswith('C') and query[1:].isdigit():
                # Code search
                row = self.df[self.df['Code'] == query]
            else:
                # Name search
                row = self.df[self.df['Display Name'].str.contains(query, case=False, na=False)]
            
            if row.empty:
                self.log(f"❌ No results found for '{query}'.\n\nTip: Try using the 'Custom Input' tab to analyze this drug manually.")
                return
            
            if len(row) > 1:
                self.log(f"⚠ Multiple matches found ({len(row)}). Using the first one: {row.iloc[0]['Display Name']}\n\nAnalyzing...")
                self.root.update()
                
            drug_input = row_to_input(row.iloc[0])
            report = generate_single_drug_report(drug_input)
            self.log(report)
            
        except Exception as e:
            self.log(f"Error during analysis: {e}")
            import traceback
            print(traceback.format_exc())

    def run_custom_analysis(self):
        name = self.entry_name.get().strip()
        desc = self.text_desc.get("1.0", tk.END).strip()
        
        if not name or not desc:
            messagebox.showwarning("Input Error", "Please provide both Name and Description.")
            return
            
        try:
            fake_row = pd.Series({
                "Display Name": name,
                "Synonyms": "",
                "Definition": desc, 
                "Concept in Subset": "",
                "Code": "CUSTOM_INPUT",
                "Semantic Type": "Pharmacologic Substance"
            })
            
            drug_input = row_to_input(fake_row)
            report = generate_single_drug_report(drug_input)
            self.log(report)
            
        except Exception as e:
            self.log(f"Error during analysis: {e}")
            import traceback
            print(traceback.format_exc())

if __name__ == "__main__":
    root = tk.Tk()
    # Set icon if available, otherwise ignore
    try:
        # root.iconbitmap("icon.ico") 
        pass
    except:
        pass
        
    app = RDRApp(root)
    root.mainloop()

import pandas as pd
import json

file_path = "C:/Agent RAB Analyzer/Rumus PPN Rincian Termin Incloude.xlsx"
try:
    xls = pd.ExcelFile(file_path)
    info = {"sheets": xls.sheet_names, "data": {}}
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        info["data"][sheet] = df.head(5).to_dict(orient="records")
    print(json.dumps(info, indent=2))
except Exception as e:
    print("Error:", e)

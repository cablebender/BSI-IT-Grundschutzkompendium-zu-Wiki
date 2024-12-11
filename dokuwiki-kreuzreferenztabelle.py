# die Kreuzreferenztabelle "krt2023_Excel.xlsx" muss im aktuellen Verzeichnis vorliegen.

import os
import pandas as pd
import unicodedata

def sanitize_name(name):
    """Konvertiert Umlaute, entfernt Sonderzeichen und wandelt den Namen in Kleinbuchstaben um."""
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')  # Entfernt Nicht-ASCII-Zeichen
    return name.lower()

def excel_to_dokuwiki(input_file, output_dir):
    """Parst eine Excel-Datei und generiert Dokuwiki-Dateien basierend auf den Tabellenblättern."""
    # Dateiname bearbeiten, um das Zielverzeichnis zu erstellen
    base_name = os.path.basename(input_file)  # Extrahiert den Dateinamen
    dir_name = sanitize_name(base_name.replace(".xlsx", ""))  # Entfernt die Endung und konvertiert den Namen
    target_dir = os.path.join(output_dir, dir_name)
    os.makedirs(target_dir, exist_ok=True)  # Erstelle das Zielverzeichnis, falls es nicht existiert
    
    # Excel-Datei laden
    excel_data = pd.ExcelFile(input_file)
    
    # Iteriere durch die Tabellenblätter
    for sheet_name in excel_data.sheet_names:
        # Lese das Tabellenblatt in ein DataFrame
        df = excel_data.parse(sheet_name)
        
        # Generiere den Dokuwiki-Inhalt
        dokuwiki_table = ""

        # Die erste Zeile als Kopfzeile verwenden
        headers = df.columns.tolist()
        headers = [str(header) for header in headers]  # Header in Strings umwandeln
        dokuwiki_table += "^ " + " ^ ".join(headers) + " ^\n"

        # Iteriere über die Zeilen und formatiere die erste Spalte als Kopfspalte
        for _, row in df.iterrows():
            row_data = row.tolist()
            row_data = [str(item) if not pd.isna(item) else "" for item in row_data]  # Konvertiere alle Werte in Strings
            first_col = row_data[0]  # Erste Spalte
            remaining_cols = row_data[1:]  # Restliche Spalten
            dokuwiki_table += f"| **{first_col}** | " + " | ".join(remaining_cols) + " |\n"
        
        # Speichere die Tabelle in einer Datei
        sheet_file_name = sanitize_name(sheet_name) + ".txt"
        output_file_path = os.path.join(target_dir, sheet_file_name.replace(".xlsx", ""))
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(dokuwiki_table)

    print(f"Dokuwiki-Dateien wurden im Verzeichnis '{target_dir}' erstellt.")

# Beispielaufruf
input_excel = "krt2023_Excel.xlsx"  # Pfad zur Excel-Datei
output_directory = "dokuwiki_pages"  # Zielverzeichnis
excel_to_dokuwiki(input_excel, output_directory)

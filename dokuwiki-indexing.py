import os
import re
import csv

# Erstellen der indexed_pages.csv
def extract_heading(file_path):
    """Extrahiert die erste Überschrift (zwischen '======') aus einer Dokuwiki-Seite."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for line in lines:
                # Sucht nach einer Überschrift, die mit '====== ... ======' formatiert ist
                match = re.match(r'^={5,}(.+?)={5,}$', line.strip())
                if match:
                    return match.group(1).strip()  # Gibt die erste gefundene Überschrift zurück
    except Exception as e:
        print(f"Fehler beim Lesen der Datei {file_path}: {e}")
    return None

def index_dokuwiki_pages(root_dir, output_file):
    """Durchsucht alle Seiten im DokuWiki-Verzeichnis und erstellt eine CSV mit Dateipfaden und Überschriften."""
    indexed_data = []

    # Geht rekursiv durch das Verzeichnis
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.txt'):  # DokuWiki-Seiten sind in der Regel .txt-Dateien
                file_path = os.path.join(root, file)
                heading = extract_heading(file_path)

                # Wenn eine Überschrift gefunden wurde, wird sie zusammen mit dem Dateipfad gespeichert
                if heading:
                    # Speichert den modifizierten Dateipfad (Endung entfernt und Schrägstrich ersetzt)
                    relative_path = os.path.relpath(file_path, root_dir)
                    relative_path = relative_path[:-4].replace("/", ":")  # ".txt" entfernen und "/" durch ":" ersetzen
                    indexed_data.append([relative_path, heading])

    # Schreibt die Daten in eine CSV-Datei
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Dateipfad,Überschrift\n")
        for entry in indexed_data:
            f.write(f"{entry[0]},{entry[1]}\n")

# Ersetzen der Texte mit Dokuwiki-Link-Syntax
def replace_with_links(root_dir, csv_file):
    """Durchläuft alle Dokuwiki-Seiten und ersetzt gefundene Texte mit Dokuwiki-Link-Syntax."""
    # Lade die Daten aus der CSV
    replacements = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Überspringe die Kopfzeile
        for row in reader:
            replacements.append((row[1], f"[[{row[0]}|{row[1]}]]"))

    # Durchlaufe alle Dateien und ersetze die Texte
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                new_lines = []
                for line in lines:
                    # Überschriften erkennen und nicht ersetzen
                    if re.match(r'^={2,}.*={2,}$', line.strip()):
                        new_lines.append(line)
                        continue

                    # Ersetze Texte mit der Dokuwiki-Link-Syntax, außer Überschriften
                    for original, replacement in replacements:
                        line = line.replace(original, replacement)
                    new_lines.append(line)

                # Schreibe die geänderten Inhalte zurück in die Datei
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)

# Hauptablauf
def main():
    # Phase 1: Erstellen der indexed_pages.csv
    base_dir = 'dokuwiki/data/pages'
    output_csv = 'indexed_pages.csv'
    index_dokuwiki_pages(base_dir, output_csv)
    print(f"Index-Datei wurde erstellt: {output_csv}")

    # Phase 2: Ersetzen der Texte mit Dokuwiki-Link-Syntax
    replace_with_links(base_dir, output_csv)
    print("Texte wurden erfolgreich ersetzt.")

if __name__ == "__main__":
    main()

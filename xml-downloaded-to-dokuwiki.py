import re
import os
import xml.etree.ElementTree as ET

def sanitize_filename(filename):
    """
    Ersetzt problematische Zeichen im Dateinamen, konvertiert zu Kleinbuchstaben,
    ersetzt Umlaute und Leerzeichen.
    """
    umlaut_map = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss'
    }
    # Umlaute ersetzen
    for umlaut, replacement in umlaut_map.items():
        filename = filename.replace(umlaut, replacement)
    # Leerzeichen durch Unterstriche ersetzen und alles in Kleinbuchstaben umwandeln
    filename = re.sub(r"\s+", "_", filename).lower()
    # Entfernt nicht alphanumerische Zeichen außer Unterstrichen, Punkten und Bindestrichen
    filename = re.sub(r"[^\w\-_\.]", "", filename)
    return filename.strip()

def extract_text_with_subtags(element):
    """
    Extrahiert Text aus einem XML-Element, einschließlich Unterelementen wie <emphasis>.
    """
    if element is None:
        return ""
    text = (element.text or "")
    for sub_element in element:
        text += extract_text_with_subtags(sub_element)
        if sub_element.tail:
            text += sub_element.tail
    return text

def process_sections(sections, namespaces, depth=2):
    """
    Verarbeitet eine Liste von <section>-Elementen und gibt sie als formatierter Text zurück.
    """
    content = ""
    for section in sections:
        # Titel der Section extrahieren
        title_element = section.find("docbook:title", namespaces)
        section_title = title_element.text if title_element is not None else "unbenannt"
        # Erstelle die passende Überschrift (Tiefe der Überschrift abhängig von `depth`)
        header = "=" * depth + f" {section_title} " + "=" * depth + "\n\n"
        content += header
        # Inhalte der aktuellen Section hinzufügen
        paras = section.findall("docbook:para", namespaces)
        content += "\n\n".join([extract_text_with_subtags(para) for para in paras if para is not None]) + "\n\n"
        # Rekursiv untergeordnete Sections verarbeiten
        subsections = section.findall("docbook:section", namespaces)
        if subsections:
            content += process_sections(subsections, namespaces, depth + 1)
    return content

def create_dokuwiki_pages_with_nested_sections(file_path, output_dir):
    try:
        # XML-Namespace definieren
        namespaces = {'docbook': 'http://docbook.org/ns/docbook'}
        
        # XML-Datei parsen
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Hauptausgabe-Verzeichnis erstellen
        os.makedirs(output_dir, exist_ok=True)
        
        # Suche nach <chapter>-Elementen im Namespace
        chapters = root.findall(".//docbook:chapter", namespaces)
        print(f"Anzahl der gefundenen <chapter>-Elemente: {len(chapters)}")
        
        if not chapters:
            return "Keine passenden <chapter>-Elemente gefunden. Überprüfe den Namespace oder die XML-Dateistruktur."
        
        total_files_created = 0  # Zähler für erstellte Dateien
        
        for chapter_idx, chapter in enumerate(chapters, start=1):
            try:
                # Kapitel-Titel extrahieren
                title_element = chapter.find("docbook:title", namespaces)
                chapter_title = title_element.text if title_element is not None else f"unbenannt_{chapter_idx}"
                
                # Sicheren Verzeichnisnamen für das Kapitel erstellen
                sanitized_chapter_name = sanitize_filename(chapter_title)
                chapter_dir = os.path.join(output_dir, sanitized_chapter_name)
                os.makedirs(chapter_dir, exist_ok=True)  # Kapitel-Verzeichnis erstellen
                
                print(f"[DEBUG] Erstelle Kapitel-Verzeichnis: {chapter_dir}")
                
                # Verarbeitung der <section>-Elemente im Kapitel
                sections = chapter.findall("docbook:section", namespaces)
                for section_idx, section in enumerate(sections, start=1):
                    try:
                        # Titel der Sektion extrahieren
                        section_title_element = section.find("docbook:title", namespaces)
                        section_title = section_title_element.text if section_title_element is not None else f"unbenannt_{section_idx}"
                        
                        # Sicheren Dateinamen für die Sektion erstellen
                        sanitized_section_title = sanitize_filename(section_title)
                        filename = f"{sanitized_section_title}.txt"
                        file_path = os.path.join(chapter_dir, filename)
                        
                        # Inhalte der Section und ihrer Subsections sammeln
                        content = process_sections([section], namespaces, depth=2)
                        
                        # Debug-Ausgabe
                        print(f"[DEBUG] Erstelle Datei: {file_path}")
                        
                        # Datei speichern
                        with open(file_path, 'w', encoding='utf-8') as page_file:
                            page_file.write(content)
                        
                        total_files_created += 1
                    except Exception as section_error:
                        print(f"[ERROR] Fehler beim Verarbeiten der Sektion {section_idx} im Kapitel '{chapter_title}': {section_error}")
            except Exception as chapter_error:
                print(f"[ERROR] Fehler beim Verarbeiten des Kapitels {chapter_idx}: {chapter_error}")
        
        print(f"Erfolgreich erstellte Dateien: {total_files_created}")
        return f"Dokuwiki-Seiten wurden in den Verzeichnissen unter '{output_dir}' erstellt."
    except ET.ParseError as e:
        return f"XML-Fehler: {e}"
    except Exception as e:
        return f"Allgemeiner Fehler: {e}"

# Verzeichnis für die Dokuwiki-Seiten
output_dir = "dokuwiki_pages"

# Verarbeitung starten
result = create_dokuwiki_pages_with_nested_sections("XML_Kompendium_2023.xml", output_dir)
print(result)

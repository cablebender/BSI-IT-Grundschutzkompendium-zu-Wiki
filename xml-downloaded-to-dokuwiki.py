import os
import requests
import xml.etree.ElementTree as ET


def sanitize_filename(filename):
    """Erstellt Dateinamen, die sicher, lesbar und klein geschrieben sind."""
    translations = str.maketrans({
        "Ä": "Ae", "ä": "ae",
        "Ö": "Oe", "ö": "oe",
        "Ü": "Ue", "ü": "ue",
        "ß": "ss",
        " ": "_"
    })
    return filename.translate(translations).strip("_").lower()


def download_xml_file(url, output_path):
    """Lädt die XML-Datei von einer URL herunter."""
    response = requests.get(url)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)

def extract_text_with_subtags(element, namespaces):
    """Extrahiert Text aus einem XML-Element, einschließlich der Inhalte von unterstützten Subtags."""
    text = ""
    if element.text:
        text += element.text.strip()

    for child in element:
        if child.tag == f"{{{namespaces['doc']}}}emphasis":
            if child.text:
                text += " " + child.text.strip() + " "  # Leerzeichen einfügen
        elif child.tag == f"{{{namespaces['doc']}}}linebreak":
            text += "\n"  # Zeilenumbruch für <linebreak>
        elif child.tag == f"{{{namespaces['doc']}}}para":
            text += extract_text_with_subtags(child, namespaces) + "\n\n"  # Absätze
        else:
            text += extract_text_with_subtags(child, namespaces)

        if child.tail:
            text += child.tail.strip()

    return text

# Funktion, um den Text aus <para> innerhalb eines <chapter> zu extrahieren
def extract_para_text_from_chapter(chapter, namespaces):
    """Extrahiert den Text aus <para> innerhalb eines <chapter>."""
    text = ""
    
    # Durchsuche alle <para>-Elemente innerhalb des <chapter> und nicht innerhalb von <section>
    for para in chapter.findall(f"{{{namespaces['doc']}}}para", namespaces):
        if para.text:
            text += para.text.strip() + "\n\n"  # Text aus <para> extrahieren und hinzufügen
    
    return text

def process_chapters(xml_root, namespaces, output_dir):
    """Verarbeitet alle <chapter>-Knoten und speichert die Texte in einer start.txt."""
    for chapter in xml_root.findall(f"{{{namespaces['doc']}}}chapter", namespaces):
        # Hole den Titel des Kapitels
        title_element = chapter.find(f".//{{{namespaces['doc']}}}title", namespaces)
        chapter_title = title_element.text.strip() if title_element is not None else "unbenanntes_kapitel"
        
        # Erstelle ein Verzeichnis basierend auf dem Kapitel-Titel
        chapter_dir = os.path.join(output_dir, sanitize_filename(chapter_title))
        os.makedirs(chapter_dir, exist_ok=True)

        # Extrahieren des Texts der <para> Elemente
        para_text = extract_para_text_from_chapter(chapter, namespaces)
        
        # Wenn Text gefunden wurde, schreibe ihn in die start.txt im Kapitel-Verzeichnis
        if para_text:
            start_file_path = os.path.join(chapter_dir, "start.txt")
            with open(start_file_path, "w", encoding="utf-8") as f:
                f.write(para_text)
            print(f"[INFO] Datei erstellt: {start_file_path}")
        else:
            print("[INFO] Keine <para>-Elemente gefunden.")

def process_chapter(chapter, base_dir, namespaces):
    """Verarbeitet ein Kapitel und erstellt die Datei 'start.txt'."""
    # Extrahieren des Titels des Kapitels (falls vorhanden)
    title_element = chapter.find(f".//{namespaces['doc']}title", namespaces)
    chapter_title = title_element.text.strip() if title_element is not None else "Unbenannt"

    # Erstellen des Verzeichnisses für das Kapitel
    chapter_dir = os.path.join(base_dir, sanitize_filename(chapter_title))
    os.makedirs(chapter_dir, exist_ok=True)

    # Extrahieren des Inhalts von <para> innerhalb des <title> Elements
    para_element = chapter.find(f".//{namespaces['doc']}para", namespaces)
    if para_element is not None:
        para_text = extract_text_with_subtags(para_element, namespaces).strip()

        # Schreiben des Inhalts in die Datei 'start.txt' im Kapitelverzeichnis
        start_file_path = os.path.join(chapter_dir, 'start.txt')
        with open(start_file_path, 'w', encoding='utf-8') as f:
            f.write(para_text)

    # Verarbeite weiter alle Untersektionen, falls vorhanden
    sections = chapter.findall(f".//{namespaces['doc']}section", namespaces)
    for section in sections:
        process_section(section, chapter_dir, namespaces)
        
def process_section(section, namespaces, depth):
    """Verarbeitet eine einzelne Sektion und erstellt den strukturierten Text."""
    text = ""
    # Berechnung der Anzahl der Gleichheitszeichen basierend auf der Dokuwiki-Syntax
    dokuwiki_depth = max(1, 6 - (depth - 1))

    # Hole den Titel der Sektion
    title_element = section.find(f"./{{{namespaces['doc']}}}title", namespaces)
    if title_element is not None:
        text += f"{'=' * dokuwiki_depth} {title_element.text.strip()} {'=' * dokuwiki_depth}\n\n"

    # Füge den Inhalt der Sektion hinzu
    for para in section.findall(f"./{{{namespaces['doc']}}}para", namespaces):
        if para.text:
            text += f"{para.text.strip()}\n\n"

    # Verarbeite Listen innerhalb der Sektion
    for itemizedlist in section.findall(f"./{{{namespaces['doc']}}}itemizedlist", namespaces):
        for listitem in itemizedlist.findall(f"./{{{namespaces['doc']}}}listitem", namespaces):
            listitem_text = extract_text_with_subtags(listitem, namespaces)
            if listitem_text:
                text += f"  * {listitem_text.strip()}\n"
        text += "\n"  # Leerzeile nach der Liste

    # Verarbeite verschachtelte Sektionen
    for subsection in section.findall(f"./{{{namespaces['doc']}}}section", namespaces):
        text += process_section(subsection, namespaces, depth + 1)

    return text



def main():
    # Herunterladen und Parsen der XML-Datei
    xml_file_path = "XML_Kompendium_2023.xml"
    if not os.path.exists(xml_file_path):
        print("[INFO] Lade XML-Datei herunter...")
        url = "https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/IT-GS-Kompendium/XML_Kompendium_2023.xml?__blob=publicationFile&v=4"
        download_xml_file(url, xml_file_path)

    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    namespaces = {"doc": "http://docbook.org/ns/docbook"}

    # Basisverzeichnis erstellen
    base_dir = "dokuwiki_pages"
    os.makedirs(base_dir, exist_ok=True)

    # Verarbeite alle <chapter> Knoten und extrahiere den Inhalt von <para>
    process_chapters(root, namespaces, base_dir)

    # Iteration durch Kapitel
    for chapter in root.findall(f"{{{namespaces['doc']}}}chapter", namespaces):
        # Kapitel-Titel
        chapter_title_element = chapter.find(f"{{{namespaces['doc']}}}title", namespaces)
        chapter_title = chapter_title_element.text.strip() if chapter_title_element is not None else "unbenanntes_kapitel"

        # Kapitel-Verzeichnis erstellen
        chapter_dir = os.path.join(base_dir, sanitize_filename(chapter_title))
        os.makedirs(chapter_dir, exist_ok=True)

        # Verarbeitung der Sektionen
        for section in chapter.findall(f"{{{namespaces['doc']}}}section", namespaces):
            # Hole den Titel der Sektion für den Dateinamen
            section_title_element = section.find(f"./{{{namespaces['doc']}}}title", namespaces)
            section_title = section_title_element.text.strip() if section_title_element is not None else "unbenannte_section"

            # Generiere den Dateinamen basierend auf dem Sektionstitel
            file_name = sanitize_filename(section_title) + ".txt"
            file_path = os.path.join(chapter_dir, file_name)

            # Verarbeite die Sektion und erstelle den Textinhalt
            section_text = process_section(section, namespaces, 1)

            # Schreibe Text in die Datei
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(section_text)

            print(f"[INFO] Datei erstellt: {file_path}")


if __name__ == "__main__":
    main()

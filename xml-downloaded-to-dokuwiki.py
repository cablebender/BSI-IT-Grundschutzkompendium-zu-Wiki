import os
import requests
import xml.etree.ElementTree as ET

def download_xml(url, filename):
    """
    Lädt die XML-Datei von der angegebenen URL herunter und speichert sie lokal.
    """
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, "wb") as file:
        file.write(response.content)

def extract_text_with_subtags(element, namespaces):
    """
    Extrahiert Text aus einem XML-Element, einschließlich verschachtelter Elemente wie <itemizedlist> und <listitem>.
    """
    if element is None:
        return ""
    
    text = (element.text or "").strip()

    for sub_element in element:
        tag = sub_element.tag.lower()

        if tag.endswith("itemizedlist"):
            for listitem in sub_element.findall(f"{{{namespaces['docbook']}}}listitem", namespaces):
                listitem_text = extract_text_with_subtags(listitem, namespaces).strip()
                if listitem_text:
                    text += f"\n  * {listitem_text}"

        elif tag.endswith("listitem"):
            listitem_text = extract_text_with_subtags(sub_element, namespaces).strip()
            if listitem_text:
                text += f"\n{listitem_text}"

        else:
            text += extract_text_with_subtags(sub_element, namespaces).strip()

        if sub_element.tail:
            text += sub_element.tail.strip()

    return text.strip()

def sanitize_filename(name):
    """
    Erzeugt einen sicheren Dateinamen:
    - Konvertiert Großbuchstaben in Kleinbuchstaben
    - Ersetzt Umlaute
    - Ersetzt Leerzeichen durch Unterstriche
    """
    translations = str.maketrans({
        "Ä": "Ae", "ä": "ae",
        "Ö": "Oe", "ö": "oe",
        "Ü": "Ue", "ü": "ue",
        "ß": "ss",
        " ": "_"
    })
    sanitized_name = name.translate(translations).lower()
    return "".join(c for c in sanitized_name if c.isalnum() or c == "_")

def process_sections(sections, chapter_dir, namespaces):
    """
    Verarbeitet alle Sections innerhalb eines Kapitels und erstellt die entsprechenden Dateien.
    """
    for section in sections:
        try:
            section_title_element = section.find(f"{{{namespaces['docbook']}}}title", namespaces)
            section_title = section_title_element.text.strip() if section_title_element is not None else "untitled_section"
            section_text = extract_text_with_subtags(section, namespaces)

            filename = sanitize_filename(section_title) + ".txt"
            filepath = os.path.join(chapter_dir, filename)

            with open(filepath, "w", encoding="utf-8") as file:
                file.write(f"====== {section_title} ======\n\n{section_text}")
        except Exception as e:
            print(f"[ERROR] Fehler beim Verarbeiten der Sektion '{section_title}': {e}")

def main():
    xml_url = "https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/IT-GS-Kompendium/XML_Kompendium_2023.xml?__blob=publicationFile&v=4"
    xml_filename = "XML_Kompendium_2023.xml"

    print("Lade XML-Datei herunter...")
    download_xml(xml_url, xml_filename)

    print("Validierung und Parsen der XML-Datei...")
    tree = ET.parse(xml_filename)
    root = tree.getroot()

    namespaces = {
        "docbook": "http://docbook.org/ns/docbook"
    }

    base_dir = "dokuwiki_pages"
    os.makedirs(base_dir, exist_ok=True)

    for chapter in root.findall(f"{{{namespaces['docbook']}}}chapter", namespaces):
        chapter_title_element = chapter.find(f"{{{namespaces['docbook']}}}title", namespaces)
        chapter_title = chapter_title_element.text.strip() if chapter_title_element is not None else "untitled_chapter"

        chapter_dir = os.path.join(base_dir, sanitize_filename(chapter_title))
        os.makedirs(chapter_dir, exist_ok=True)

        print(f"Verarbeite Kapitel: {chapter_title}")

        sections = chapter.findall(f"{{{namespaces['docbook']}}}section", namespaces)
        process_sections(sections, chapter_dir, namespaces)

    print("Verarbeitung abgeschlossen!")

if __name__ == "__main__":
    main()

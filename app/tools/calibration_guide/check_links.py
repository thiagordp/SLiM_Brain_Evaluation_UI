"""Check that every internal hyperlink in a .docx points to an existing bookmark.

    python app/tools/calibration_guide/check_links.py FILE.docx [...]
"""
import sys
import zipfile

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
bad = 0
for path in sys.argv[1:]:
    doc = etree.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
    marks = {b.get(W + "name") for b in doc.iter(W + "bookmarkStart")}
    links = [h.get(W + "anchor") for h in doc.iter(W + "hyperlink") if h.get(W + "anchor")]
    missing = sorted({a for a in links if a not in marks})
    print(f"{path}: {len(links)} internal links, {len(marks)} bookmarks, {len(missing)} broken {missing}")
    bad += len(missing)
sys.exit(1 if bad else 0)

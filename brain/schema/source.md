# Node: Source

One node per publication in the corpus.

## Fields

- **`id`** — prefixed `SRC-`, stable, never reused; consumed only when the record is first written. Example: `SRC-0001`.

- **`file`** — path of the markdown conversion from the repository root, inside the input folder the batch was given (CLAUDE.md, *Running an ingest*), e.g. `raw/SRC-0012.md`.

- **`conversion_tool`** — tool and version used for the PDF-to-markdown conversion, with parameters; copy the exact string from the input folder's `_conversions.json`, e.g. "docling 2.123.1, tools/convert_source.py, ocr=off, table_structure=on".

- **`title`** — from the document text, never from the filename (filenames never enter the graph as titles).

- **`authors`** — as printed, family name first.

- **`year`** — year of publication.

- **`venue`** — journal, conference, publisher, or repository.

- **`venue_type`** — one of `journal` | `conference` | `book_chapter` | `working_paper` | `preprint` | `report` | `thesis` | `other` | `unknown`. `other` is a venue of a kind not listed; `unknown` is for a document that states no venue at all.

- **`language`** — ISO 639-1 code of the main text.

- **`doi`** - the paper's DOI identifier, if available.

- **`publication_date`** - the paper's publication date.

- **`run_ids`** — `schema/run.md`.




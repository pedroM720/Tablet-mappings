# Tablet Mappings: Finding Old Assyrian Tablets in HeiCuBeDa

A specialized digital epigraphy and metadata-alignment project linking Old Assyrian cuneiform tablets from the Hilprecht Collection to the Heidelberg Cuneiform Benchmark Dataset (**HeiCuBeDa**) and the Mainz Cuneiform Benchmark Knowledge Graph (**MaiCuBeDa**).

---

## 1. Overview & Objective

This project cross-references the Frau Professor Hilprecht Collection (*Hilprecht-Sammlung Vorderasiatischer Altertümer*, Friedrich Schiller University Jena) Old Assyrian merchant archive catalog against the HeiCuBeDa 2D/3D cuneiform benchmark dataset without requiring heavy 3D mesh downloads.

### Core Bridge Identifiers:
- **Museum Inventory Number**: Alphanumeric museum identifiers with the `HS` prefix (e.g., `HS 440`, `HS 289`, `HS 293a`).
- **CDLI P-number**: Cuneiform Digital Library Initiative accession number (e.g., `P358045`).
- **Knowledge Graph QID**: FactGrid / Epigraphy Knowledge Graph item identifier (e.g., `Q1371460` - `Q1371580`).
- **HeidICON IIIF Image Pointers**: Direct 2D IIIF high-resolution raster image links to tablet faces on Heidelberg University servers.
- **MaiCuBeDa RDF URIs**: CIDOC-CRM (`cunei:Tablet`, `cidoc:TX1_WrittenText`) and Lemon (`lemon:Character`) entities in `maicubeda.ttl`.

---

## 2. Project Structure

```
Tablet mappings/
├── generate_mapping.py                  # Primary reproducible pipeline script
├── old_assyrian_heicubeda_mapping.csv   # Unified alignment mapping (all 121 Hilprecht records, status flagged)
├── old_assyrian_heicubeda_matched_only.csv # Subset of the 44 matched tablets with full epigraphic pointers
└── README.md                            # Project documentation and schema reference
```

---

## 3. Dataset Summary & Alignment Metrics

| Metric | Value | Description |
| :--- | :--- | :--- |
| **Hilprecht Catalog Records** | **121** | 100% Old Assyrian period (`Q512151`), Hilprecht Collection (`Q511931`) |
| **Unique Physical Objects (CDLI)** | **111** | 101 single tablets + 10 tablet-envelope pairs (20 rows) |
| **HeiCuBeDa Total Tablets** | **591** | Multi-period benchmark corpus |
| **MaiCuBeDa Total Tablets** | **591** | Exactly matches HeiCuBeDa CDLI set |
| **Old Assyrian Tablets in HeiCuBeDa** | **44** | 100% trace to the Hilprecht catalog (0 orphan OA records) |
| **Match Success Rate** | **36.36%** | **44 matched / 77 unlinked** (39.64% of unique CDLI numbers) |
| **Sign Annotations Linked** | **2,902** | 100% of Old Assyrian 2D sign bounding boxes |
| **RDF Character Nodes Linked** | **1,915** | Character entities across 181 distinct cuneiform glyph classes |

---

## 4. Key Epigraphic Findings & Discrepancies

1. **Benchmark Boundary**:
   - Exactly 44 Old Assyrian tablets were included in the HeiCuBeDa benchmark. All 44 match the Hilprecht catalog.
   - The remaining 77 catalog entries represent Old Assyrian tablets not selected for the 591-tablet Heidelberg/Mainz 3D digitization campaign.
2. **Tablet & Envelope Pairs (`unique? = FALSE`)**:
   - 20 rows in the Hilprecht catalog represent 10 composite tablet-envelope pairs sharing CDLI numbers (e.g. `P358112`, `P358119`). All 44 tablets selected in HeiCuBeDa are standalone tablets.
3. **Missing OARe Edition (Row 118)**:
   - Row 118 (`Q1371578`, CDLI `P358163`, `HS 434`, `TMH 1 18c`) lacks an OARe ID and transcript URL, carrying audit flags `dataset_complaint: Q961353 | Q750602`.
4. **Scan Resolutions**:
   - HeiCuBeDa scan IDs reflect scanner resolutions: `_03` (0.3 mm) and `_06` (0.06 mm).

---

## 5. Running the Pipeline

Run the pipeline using Python 3:

```bash
# Run from within the project directory:
python generate_mapping.py

# Or specify custom source data and output directories:
python generate_mapping.py --data-dir "C:/path/to/data" --output-dir "C:/path/to/output"
```

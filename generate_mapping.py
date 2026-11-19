"""
Cross-Reference Mapping Pipeline: Finding Old Assyrian Tablets in HeiCuBeDa

Links the Hilprecht Collection Old Assyrian cuneiform tablet catalog to:
- HeiCuBeDa (Heidelberg Cuneiform Benchmark Dataset - translitmetadata.csv)
- MaiCuBeDa (Mainz Cuneiform Benchmark Knowledge Graph - maicubeda.ttl)
"""

import os
import sys
import csv
import re
import collections
import argparse

def run_pipeline(data_dir=None, output_dir=None):
    if data_dir is None:
        data_dir = r"C:\Users\sacii\Downloads"
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    hillprecht_path = os.path.join(data_dir, "Hillprecht_Collection_HeiCuBeDa - Sheet1.csv")
    translit_path = os.path.join(data_dir, "translitmetadata.csv")
    ttl_path = os.path.join(data_dir, "maicubeda.ttl")

    print(f"Data directory:   {data_dir}")
    print(f"Output directory: {output_dir}")

    # 1. Parse translitmetadata.csv
    print("Parsing translitmetadata.csv...")
    translit_data = collections.defaultdict(lambda: {
        'scan_ids': set(),
        'crop_filenames': set(),
        'heidicon_base_urls': set(),
        'heidicon_sample_urls': set(),
        'sign_count': 0,
        'sign_names': collections.Counter(),
        'transliteration_samples': []
    })

    with open(translit_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        for row in reader:
            if not row:
                continue
            cdli = row[2].strip() if len(row) > 2 else ''
            period = row[5].strip() if len(row) > 5 else ''
            if cdli and 'old assyrian' in period.lower():
                td = translit_data[cdli]
                scan_id = row[0].strip()
                if scan_id:
                    td['scan_ids'].add(scan_id)
                if len(row) > 1 and row[1].strip():
                    td['crop_filenames'].add(row[1].strip())
                if len(row) > 4 and row[4].strip():
                    raw_url = row[4].strip()
                    m_base = re.search(r'(https://heidicon\.ub\.uni-heidelberg\.de/iiif/2/[^/]+)', raw_url)
                    if m_base:
                        td['heidicon_base_urls'].add(f"{m_base.group(1)}/full/full/0/default.jpg")
                    if len(td['heidicon_sample_urls']) < 3:
                        td['heidicon_sample_urls'].add(raw_url)
                td['sign_count'] += 1
                if len(row) > 13 and row[13].strip():
                    td['sign_names'][row[13].strip()] += 1
                if len(row) > 14 and row[14].strip():
                    if len(td['transliteration_samples']) < 8:
                        td['transliteration_samples'].append(row[14].strip())

    print(f"Loaded translitmetadata for {len(translit_data)} Old Assyrian tablets ({sum(t['sign_count'] for t in translit_data.values())} sign occurrences).")

    # 2. Parse maicubeda.ttl
    print("Parsing maicubeda.ttl...")
    ttl_tablets = {}
    ttl_texts = {}
    ttl_characters = collections.defaultdict(set)
    ttl_glyphs_found = collections.defaultdict(set)

    re_tab = re.compile(r'<http://cdli\.ucla\.edu/(P\d{6})>\s+rdf:type\s+cunei:Tablet')
    re_txt = re.compile(r'<http://cdli\.ucla\.edu/(P\d{6})_text>\s+rdf:type\s+cidoc:TX1_WrittenText')
    re_char = re.compile(r'<http://cdli\.ucla\.edu/(P\d{6})_char_([^>]+)>')
    re_glyph = re.compile(r'<http://cdli\.ucla\.edu/([^>]+)>\s+cidoc:P56_isFoundOn\s+<http://cdli\.ucla\.edu/(P\d{6})>')

    with open(ttl_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line_clean = line.strip()
            if not line_clean or line_clean.startswith('@prefix'):
                continue
            
            m = re_tab.search(line_clean)
            if m:
                p = m.group(1)
                ttl_tablets[p] = f"http://cdli.ucla.edu/{p}"
                continue
                
            m = re_txt.search(line_clean)
            if m:
                p = m.group(1)
                ttl_texts[p] = f"http://cdli.ucla.edu/{p}_text"
                continue
                
            m = re_char.search(line_clean)
            if m:
                p, c_id = m.groups()
                ttl_characters[p].add(c_id)
                
            m = re_glyph.search(line_clean)
            if m:
                glyph, p = m.groups()
                ttl_glyphs_found[p].add(glyph)

    print(f"Loaded TTL: {len(ttl_tablets)} tablet definitions, {len(ttl_texts)} text definitions, {len(ttl_characters)} tablets with characters.")

    # 3. Parse Hillprecht catalog
    print("Parsing Hillprecht catalog...")
    with open(hillprecht_path, 'r', encoding='utf-8', errors='replace') as f:
        hp_rows = list(csv.DictReader(f))

    print(f"Total rows in Hillprecht collection catalog: {len(hp_rows)}")

    # Build alignment records
    output_rows = []

    for idx, r in enumerate(hp_rows):
        qid = r.get('Qid', '').strip()
        cdli = r.get('cdli_id', '').strip()
        inv_pos = r.get('inventory_position (string)', '').strip()
        pub_dedup = r.get('publication_catalog_dedup', '').strip()
        tmh_alias = r.get('alias2', '').strip()
        obj_type = r.get('object_type', '').strip()
        oare_id = r.get('oare_id', '').strip()
        oare_transcript = r.get('online transcript', '').strip()
        cdli_photo = r.get('P188', '').strip()
        aicc_url = r.get('AICC translation', '').strip()
        dataset_complaint = r.get('dataset_complaint', '').strip()
        is_unique = r.get('unique?', '').strip()
        archive = r.get('archive', '').strip()
        dossier = r.get('dossier', '').strip()
        
        hs_num = pub_dedup if pub_dedup else inv_pos
        is_matched = cdli in translit_data
        td = translit_data.get(cdli, None)
        
        heicubeda_ids_str = "; ".join(sorted(td['scan_ids'])) if td else "None"
        sign_count = td['sign_count'] if td else 0
        
        maicubeda_tab_uri = ttl_tablets.get(cdli, "None") if is_matched else "None"
        maicubeda_txt_uri = ttl_texts.get(cdli, "None") if is_matched else "None"
        char_count = len(ttl_characters.get(cdli, set())) if is_matched else 0
        glyph_type_count = len(ttl_glyphs_found.get(cdli, set())) if is_matched else 0
        
        dataset_refs_list = []
        if td and td['heidicon_base_urls']:
            base_urls_str = " | ".join(sorted(td['heidicon_base_urls']))
            dataset_refs_list.append(f"HeiCuBeDa HeidICON IIIF: {base_urls_str}")
        if cdli_photo:
            dataset_refs_list.append(f"CDLI Photo: {cdli_photo}")
        if oare_transcript:
            dataset_refs_list.append(f"OARe Transcript URL: {oare_transcript}")
        elif oare_id:
            dataset_refs_list.append(f"OARe ID: {oare_id}")
        dataset_references = " ; ".join(dataset_refs_list) if dataset_refs_list else "None"
        
        translit_ptrs_list = []
        if td:
            sample_str = ", ".join(td['transliteration_samples'][:6])
            top_signs = ", ".join([f"{k} (x{v})" for k, v in td['sign_names'].most_common(4)])
            translit_ptrs_list.append(f"HeiCuBeDa: {sign_count} sign annotations (Top signs: {top_signs}; Sample readings: {sample_str})")
        else:
            translit_ptrs_list.append("HeiCuBeDa: Not in benchmark dataset")
            
        if oare_transcript:
            translit_ptrs_list.append(f"OARe Edition: {oare_transcript}")
        if aicc_url:
            translit_ptrs_list.append(f"AICC Translation Portal: {aicc_url}")
        transliteration_pointers = " ; ".join(translit_ptrs_list)
        
        discrepancies = []
        if not is_matched:
            discrepancies.append("Unlinked to HeiCuBeDa (tablet was not selected in Heidelberg/Mainz 3D benchmark)")
        if is_unique == 'FALSE':
            discrepancies.append("Multi-part artifact (tablet/envelope pair sharing CDLI number)")
        if dataset_complaint:
            discrepancies.append(f"Catalog flagged dataset complaint ({dataset_complaint})")
        if not oare_id and not oare_transcript:
            discrepancies.append("Missing OARe identifier and online transcript")
        
        notes_str = "; ".join(discrepancies) if discrepancies else "Clean alignment; full match"
        
        row_dict = {
            'catalog_index': idx + 1,
            'museum_inventory_hs': hs_num,
            'cdli_pnumber': cdli,
            'heicubeda_kg_qid': qid,
            'publication_designation': tmh_alias,
            'object_type': obj_type,
            'period': "Old Assyrian Period (ca. 1950-1850 BC)",
            'heicubeda_status': "MATCHED" if is_matched else "UNLINKED",
            'heicubeda_scan_ids': heicubeda_ids_str,
            'heicubeda_sign_count': sign_count,
            'maicubeda_tablet_uri': maicubeda_tab_uri,
            'maicubeda_text_uri': maicubeda_txt_uri,
            'maicubeda_char_nodes_count': char_count,
            'maicubeda_glyph_types_count': glyph_type_count,
            'dataset_references': dataset_references,
            'transliteration_pointers': transliteration_pointers,
            'oare_id': oare_id if oare_id else "N/A",
            'archive_context': f"{archive} {dossier}".strip() if (archive or dossier) else "N/A",
            'notes_and_discrepancies': notes_str
        }
        output_rows.append(row_dict)

    output_rows_sorted = sorted(output_rows, key=lambda x: (0 if x['heicubeda_status'] == 'MATCHED' else 1, x['cdli_pnumber']))

    fieldnames = [
        'catalog_index',
        'museum_inventory_hs',
        'cdli_pnumber',
        'heicubeda_kg_qid',
        'publication_designation',
        'object_type',
        'period',
        'heicubeda_status',
        'heicubeda_scan_ids',
        'heicubeda_sign_count',
        'maicubeda_tablet_uri',
        'maicubeda_text_uri',
        'maicubeda_char_nodes_count',
        'maicubeda_glyph_types_count',
        'dataset_references',
        'transliteration_pointers',
        'oare_id',
        'archive_context',
        'notes_and_discrepancies'
    ]

    # Write old_assyrian_heicubeda_mapping.csv
    mapping_csv_path = os.path.join(output_dir, "old_assyrian_heicubeda_mapping.csv")
    with open(mapping_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows_sorted)
    print(f"Saved complete alignment mapping: {mapping_csv_path}")

    # Write old_assyrian_heicubeda_matched_only.csv
    matched_only_rows = [r for r in output_rows_sorted if r['heicubeda_status'] == 'MATCHED']
    matched_csv_path = os.path.join(output_dir, "old_assyrian_heicubeda_matched_only.csv")
    with open(matched_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matched_only_rows)
    print(f"Saved matched-only subset mapping: {matched_csv_path}")

    print("\n--- Summary Statistics ---")
    print(f"Total Hilprecht Old Assyrian rows: {len(output_rows)}")
    print(f"HeiCuBeDa MATCHED tablets:         {len(matched_only_rows)} ({len(matched_only_rows)/len(output_rows)*100:.2f}%)")
    print(f"HeiCuBeDa UNLINKED tablets:        {len(output_rows) - len(matched_only_rows)} ({(len(output_rows) - len(matched_only_rows))/len(output_rows)*100:.2f}%)")
    print(f"Total annotated signs linked:      {sum(r['heicubeda_sign_count'] for r in matched_only_rows)}")
    print(f"Total RDF character nodes:         {sum(r['maicubeda_char_nodes_count'] for r in matched_only_rows)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Cross-reference Hilprecht Old Assyrian tablets with HeiCuBeDa")
    parser.add_argument("--data-dir", default=r"C:\Users\sacii\Downloads", help="Directory containing source data files")
    parser.add_argument("--output-dir", default=None, help="Directory to save output mapping CSVs")
    args = parser.parse_args()

    run_pipeline(args.data_dir, args.output_dir)

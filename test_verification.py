import os
import sys
import py_compile
import csv
import re
import unittest

PROJECT_DIR = r"C:\Users\sacii\Downloads\Tablet mappings"
DATA_DIR = r"C:\Users\sacii\Downloads"

class TestTabletMappingsDoublePass(unittest.TestCase):

    def test_01_script_compilation(self):
        """Pass 1.1: Verify Python compilation of generate_mapping.py"""
        script_path = os.path.join(PROJECT_DIR, "generate_mapping.py")
        self.assertTrue(os.path.exists(script_path), "generate_mapping.py must exist")
        # py_compile checks syntax and bytecode compilation
        compiled = py_compile.compile(script_path, doraise=True)
        self.assertIsNotNone(compiled, "Bytecode compilation should succeed")

    def test_02_pipeline_reproducibility(self):
        """Pass 1.2: Re-run pipeline and verify output files generation"""
        from generate_mapping import run_pipeline
        run_pipeline(data_dir=DATA_DIR, output_dir=PROJECT_DIR)
        
        mapping_file = os.path.join(PROJECT_DIR, "old_assyrian_heicubeda_mapping.csv")
        matched_file = os.path.join(PROJECT_DIR, "old_assyrian_heicubeda_matched_only.csv")
        self.assertTrue(os.path.exists(mapping_file), "Mapping CSV must exist")
        self.assertTrue(os.path.exists(matched_file), "Matched-only CSV must exist")

    def test_03_full_mapping_schema_and_counts(self):
        """Pass 2.1: Verify full mapping schema, row counts, and statuses"""
        mapping_file = os.path.join(PROJECT_DIR, "old_assyrian_heicubeda_mapping.csv")
        expected_fields = [
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

        with open(mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.assertEqual(reader.fieldnames, expected_fields, "Header fields must match exact specification")
            rows = list(reader)
            
        self.assertEqual(len(rows), 121, "Total catalog rows must be exactly 121")
        
        matched_rows = [r for r in rows if r['heicubeda_status'] == 'MATCHED']
        unlinked_rows = [r for r in rows if r['heicubeda_status'] == 'UNLINKED']
        
        self.assertEqual(len(matched_rows), 44, "Exactly 44 tablets must be MATCHED")
        self.assertEqual(len(unlinked_rows), 77, "Exactly 77 records must be UNLINKED")
        
        # Check that MATCHED rows are sorted first
        for i in range(44):
            self.assertEqual(rows[i]['heicubeda_status'], 'MATCHED')
        for i in range(44, 121):
            self.assertEqual(rows[i]['heicubeda_status'], 'UNLINKED')

    def test_04_identifier_integrity(self):
        """Pass 2.2: Validate CDLI, HS, QID, and Period format across all rows"""
        mapping_file = os.path.join(PROJECT_DIR, "old_assyrian_heicubeda_mapping.csv")
        with open(mapping_file, 'r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
            
        p_pattern = re.compile(r'^P\d{6}$')
        q_pattern = re.compile(r'^Q\d+$')
        
        for idx, r in enumerate(rows):
            cdli = r['cdli_pnumber']
            self.assertTrue(p_pattern.match(cdli), f"Row {idx} invalid CDLI: {cdli}")
            
            qid = r['heicubeda_kg_qid']
            self.assertTrue(q_pattern.match(qid), f"Row {idx} invalid QID: {qid}")
            
            hs = r['museum_inventory_hs']
            self.assertTrue('HS' in hs, f"Row {idx} missing HS prefix: {hs}")
            
            period = r['period']
            self.assertEqual(period, "Old Assyrian Period (ca. 1950-1850 BC)")

    def test_05_matched_tablets_deep_verification(self):
        """Pass 2.3: Verify deep epigraphic metrics and pointers for matched tablets"""
        matched_file = os.path.join(PROJECT_DIR, "old_assyrian_heicubeda_matched_only.csv")
        with open(matched_file, 'r', encoding='utf-8') as f:
            matched_rows = list(csv.DictReader(f))
            
        self.assertEqual(len(matched_rows), 44, "Matched file must have 44 rows")
        
        total_signs = sum(int(r['heicubeda_sign_count']) for r in matched_rows)
        self.assertEqual(total_signs, 2902, "Total HeiCuBeDa sign annotations must be exactly 2902")
        
        total_chars = sum(int(r['maicubeda_char_nodes_count']) for r in matched_rows)
        self.assertEqual(total_chars, 1915, "Total MaiCuBeDa character nodes must be exactly 1915")
        
        for r in matched_rows:
            # Check scan IDs format
            scan_ids = r['heicubeda_scan_ids']
            self.assertTrue('HS_' in scan_ids, f"Scan ID missing HS_: {scan_ids}")
            
            # Check URIs
            self.assertTrue(r['maicubeda_tablet_uri'].startswith("http://cdli.ucla.edu/P"), "Tablet URI invalid")
            self.assertTrue(r['maicubeda_text_uri'].endswith("_text"), "Text URI invalid")
            
            # Check HeidICON IIIF reference
            self.assertIn("HeiCuBeDa HeidICON IIIF:", r['dataset_references'])
            self.assertIn("https://heidicon.ub.uni-heidelberg.de/iiif/2/", r['dataset_references'])
            
            # Check transliteration pointer
            self.assertIn("HeiCuBeDa:", r['transliteration_pointers'])

    def test_06_unlinked_tablets_integrity(self):
        """Pass 2.4: Verify unlinked rows have clean fallback pointers and notes"""
        mapping_file = os.path.join(PROJECT_DIR, "old_assyrian_heicubeda_mapping.csv")
        with open(mapping_file, 'r', encoding='utf-8') as f:
            unlinked = [r for r in csv.DictReader(f) if r['heicubeda_status'] == 'UNLINKED']
            
        self.assertEqual(len(unlinked), 77)
        for r in unlinked:
            self.assertEqual(r['heicubeda_scan_ids'], "None")
            self.assertEqual(int(r['heicubeda_sign_count']), 0)
            self.assertEqual(r['maicubeda_tablet_uri'], "None")
            self.assertEqual(r['maicubeda_text_uri'], "None")
            self.assertEqual(int(r['maicubeda_char_nodes_count']), 0)
            self.assertIn("Unlinked to HeiCuBeDa", r['notes_and_discrepancies'])

    def test_07_special_cases(self):
        """Pass 2.5: Verify known catalog anomalies (multi-parts and row 118)"""
        mapping_file = os.path.join(PROJECT_DIR, "old_assyrian_heicubeda_mapping.csv")
        with open(mapping_file, 'r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
            
        # Row 118 check (P358163, HS 434)
        r118_matches = [r for r in rows if r['cdli_pnumber'] == 'P358163']
        self.assertEqual(len(r118_matches), 1)
        r118 = r118_matches[0]
        self.assertEqual(r118['oare_id'], 'N/A')
        self.assertIn("Missing OARe identifier", r118['notes_and_discrepancies'])
        self.assertIn("Q961353", r118['notes_and_discrepancies'])
        
        # Multi-part pairs check
        multi_parts = [r for r in rows if "Multi-part artifact" in r['notes_and_discrepancies']]
        self.assertEqual(len(multi_parts), 20, "Must be exactly 20 multi-part tablet/envelope rows")

if __name__ == '__main__':
    unittest.main()

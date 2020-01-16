import unittest
import feather
import tempfile
import os

class TestMain(unittest.TestCase):
    def test_parse_doc_entries(self):
        data = ('$ENTRY\n'
                'list=entries\n'
                'props=note,purpose\n'
                'ext=hpp,cpp\n'
                'format=.*\\s+([^(]*)\\(.*\\)\n'
                '$END\n')
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, '.feather')
            path1 = os.path.join(temp, 'templ.jinja2')
            with open(path, encoding='utf-8', mode='w') as fp:
                fp.write(data)
            with open(path1, encoding='utf-8', mode='w') as fp:
                fp.write('')
            doc_entries, templates = feather.parse_doc_entries(temp)
            self.assertEqual(1, len(doc_entries))
            entry = doc_entries[0]
            self.assertEqual('entries', entry.list_name)
            self.assertIn('note', entry.props)
            self.assertIn('purpose', entry.props)
            self.assertIn('hpp', entry.files)
            self.assertIn('cpp', entry.files)
            self.assertIn(os.path.join(temp, 'templ.jinja2'), templates)

    def test_parse_code_entry(self):
        data = ('$ENTRY\n'
                'list=entries\n'
                'props=note,purpose\n'
                'ext=hpp,cpp\n'
                'format=.*\\s+([^(]*)\\(.*\\)\n'
                '$END\n')
        cpp_file = ('Lorem ipsum\n'
                    'asdwertyui\n'
                    '\n'
                    '\n'
                    '/*\n'
                    'note: This is a note.\n'
                    'purpose: Nothing.*/\n'
                    'void function(int x)\n'
                    '{\n'
                    '}\n')
        with tempfile.TemporaryDirectory() as temp:
            path1 = os.path.join(temp, '.feather')
            path2 = os.path.join(temp, 'source.cpp')
            with open(path1, encoding='utf-8', mode='w') as fp:
                fp.write(data)
            with open(path2, encoding='utf-8', mode='w') as fp:
                fp.write(cpp_file)
            doc_entries, templates = feather.parse_doc_entries(temp)

            code_entries = {}
            feather.parse_code_entries_from_file(path2, doc_entries, code_entries)
            self.assertIn('entries', code_entries)
            self.assertIn('note', code_entries['entries'][0])
            self.assertIn('purpose', code_entries['entries'][0])
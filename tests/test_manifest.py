import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('manifest', Path(__file__).parents[1] / 'scripts/pair_manifest.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ManifestTests(unittest.TestCase):
    def test_samples(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'a.svg', Path(d)/'b.svg'
            a.write_text('<svg><text>DEMO 12PC</text></svg>')
            b.write_bytes(a.read_bytes())
            original = a.read_bytes()
            self.assertTrue(m.compare(a,b)['same_bytes'])
            self.assertFalse(m.compare(a,b)['same_file'])
            self.assertTrue(m.compare(a,a)['same_file'])
            b.write_text('<svg><text>DEMO 24PC</text></svg>')
            self.assertFalse(m.compare(a,b)['same_bytes'])
            self.assertEqual(a.read_bytes(),original)
            with self.assertRaises(ValueError): m.inspect(d)
            with self.assertRaises(ValueError): m.inspect(Path(d)/'missing')
            link = Path(d)/'link'; link.symlink_to(a)
            with self.assertRaises(ValueError): m.inspect(link)

if __name__ == '__main__': unittest.main()

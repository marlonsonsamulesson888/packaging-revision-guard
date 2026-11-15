import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('compare_files', Path(__file__).parents[1] / 'scripts/compare_files.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Checks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.a = Path(self.temp.name) / 'before'
        self.b = Path(self.temp.name) / 'after'
        self.a.mkdir(); self.b.mkdir()
    def pair(self, name, a, b):
        (self.a/name).write_text(a)
        (self.b/name).write_text(b)
    def test_same(self):
        self.pair('a.svg', '<svg/>', '<svg/>')
        self.assertEqual(m.compare(self.a, self.b)['changes'], [])
    def test_allowed_not_design_approval(self):
        self.pair('art.svg', '<svg/>', '<svg><text>changed</text></svg>')
        r = m.compare(self.a, self.b, ['art.svg'])
        self.assertEqual(r['unexpected_changes'], 0)
        self.assertEqual(r['design_acceptance'], 'not-assessed')
    def test_unexpected(self):
        self.pair('protected.txt', '24PC', '12PC')
        self.assertEqual(m.compare(self.a, self.b)['unexpected_changes'], 1)
    def test_added_removed_hidden_unicode(self):
        (self.a/'旧稿.svg').write_text('a')
        (self.b/'.hidden').write_text('b')
        r = m.compare(self.a, self.b)
        self.assertEqual(r['unexpected_changes'], 2)
        self.assertEqual({c['kind'] for c in r['changes']}, {'added', 'removed'})
    def test_missing(self):
        with self.assertRaises(ValueError): m.compare(self.a/'missing', self.b)
    def test_invalid_allow(self):
        for value in ['../secret', '/etc/passwd', 'x/../y', 'C:/x', 'a\\b', './x']:
            with self.assertRaises(ValueError): m.compare(self.a, self.b, [value])
    def test_symlink_rejected(self):
        (self.a/'link').symlink_to(self.b, target_is_directory=True)
        with self.assertRaises(ValueError): m.compare(self.a, self.b)
    def test_preserves_bytes(self):
        self.pair('art.svg', '<svg/>', '<svg>new</svg>')
        before = [(p, p.read_bytes()) for d in (self.a, self.b) for p in d.iterdir()]
        m.compare(self.a, self.b)
        self.assertTrue(all(p.read_bytes() == data for p, data in before))

if __name__ == '__main__': unittest.main()

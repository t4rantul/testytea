import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_bundle import BundleError, apply, parse

class BundleTests(unittest.TestCase):
    def test_write_and_escape_directive(self):
        bundle = parse("%%% basalt-bundle 1\n%%% message Add a note\n%%% write docs/note.txt\n%%%% literal directive\n")
        with tempfile.TemporaryDirectory() as tmp:
            apply(bundle, Path(tmp))
            self.assertEqual((Path(tmp)/"docs/note.txt").read_text(), "%%% literal directive\n")

    def test_exact_edit(self):
        bundle = parse("%%% basalt-bundle 1\n%%% message Edit\n%%% edit a.txt\n%%% search\nold\n%%% replace\nnew\n%%% end\n")
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"a.txt"; p.write_text("before old after\n")
            apply(bundle,Path(tmp)); self.assertEqual(p.read_text(),"before new after\n")

    def test_indentation_tolerant_edit(self):
        bundle = parse("%%% basalt-bundle 1\n%%% message Edit\n%%% edit a.cpp\n%%% search\nint value;\n%%% replace\nint value = 2;\n%%% end\n")
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"a.cpp"; p.write_text("  int value;\nnext();\n")
            apply(bundle,Path(tmp)); self.assertEqual(p.read_text(),"  int value = 2;\nnext();\n")

    def test_duplicate_edit_rejected_without_partial_write(self):
        bundle = parse("%%% basalt-bundle 1\n%%% message Edit\n%%% edit a.txt\n%%% search\nx\n%%% replace\ny\n%%% end\n%%% write b.txt\ncontents\n")
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/"a.txt").write_text("x x\n")
            with self.assertRaises(BundleError): apply(bundle,root)
            self.assertFalse((root/"b.txt").exists())
            self.assertEqual((root/"a.txt").read_text(),"x x\n")

    def test_search_all(self):
        bundle=parse("%%% basalt-bundle 1\n%%% message Edit\n%%% edit a.txt\n%%% search all\nx\n%%% replace\ny\n%%% end\n")
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"a.txt"; p.write_text("x x\n")
            apply(bundle,Path(tmp)); self.assertEqual(p.read_text(),"y y\n")

    def test_remove_single_indented_line(self):
        bundle=parse("%%% basalt-bundle 1\n%%% message Edit\n%%% edit a.txt\n%%% search\nremove me\n%%% replace\n%%% end\n")
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"a.txt"; p.write_text("keep\n  remove me\nlast\n")
            apply(bundle,Path(tmp)); self.assertEqual(p.read_text(),"keep\nlast\n")

    def test_rename_and_delete(self):
        bundle=parse("%%% basalt-bundle 1\n%%% message Rename\n%%% rename old.txt new.txt\n%%% delete gone.txt\n")
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/"old.txt").write_text("x"); (root/"gone.txt").write_text("z")
            apply(bundle,root); self.assertEqual((root/"new.txt").read_text(),"x")
            self.assertFalse((root/"old.txt").exists()); self.assertFalse((root/"gone.txt").exists())

    def test_unsafe_paths_rejected(self):
        for path in ("../outside", "/etc/passwd", "Incoming/payload.bundle", ".github/workflows/evil.yml", ".git/config"):
            with self.subTest(path=path):
                with self.assertRaises(BundleError): parse(f"%%% basalt-bundle 1\n%%% message Bad\n%%% write {path}\nx\n")

    def test_duplicate_paths_rejected(self):
        with self.assertRaises(BundleError):
            parse("%%% basalt-bundle 1\n%%% message Bad\n%%% write a\nx\n%%% delete a\n")

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root=Path(tmp)
            try:
                (root/"escape").symlink_to(outside,target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            bundle=parse("%%% basalt-bundle 1\n%%% message Bad\n%%% write escape/out.txt\nx\n")
            with self.assertRaises(BundleError): apply(bundle,root)
            self.assertFalse((Path(outside)/"out.txt").exists())

if __name__ == "__main__":
    unittest.main()

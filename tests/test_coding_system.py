"""Unit tests for ZYRA Polyglot Coding System."""
import unittest
import shutil
from pathlib import Path

from zyra.coding.languages import detect_language, normalize_filename, LANGUAGES
from zyra.coding.coder_engine import coder_engine
from zyra.coding.ide_manager import ide_manager
from zyra.coding.online_compiler import online_compiler
from zyra.coding.runner import code_runner
from zyra.coding.coordinator import coding_coordinator

class TestCodingSystem(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(__file__).resolve().parent / "coding_test_scratch"
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # 1. Language Detection & Normalization
    def test_language_detection(self):
        self.assertEqual(detect_language("write Java code").name, "Java")
        self.assertEqual(detect_language("create main.py").name, "Python")
        self.assertEqual(detect_language("solve in C++").name, "C++")
        self.assertEqual(detect_language("write a rust function").name, "Rust")
        self.assertEqual(detect_language("create typescript app").name, "TypeScript")
        self.assertEqual(detect_language("golang concurrency").name, "Go")
        self.assertEqual(detect_language("select query in sql").name, "SQL")

    def test_normalize_filename(self):
        java_spec = LANGUAGES["java"]
        self.assertEqual(normalize_filename("TwoSum", java_spec), "TwoSum.java")
        self.assertEqual(normalize_filename("Solution.java", java_spec), "Solution.java")

        py_spec = LANGUAGES["python"]
        self.assertEqual(normalize_filename("search", py_spec), "search.py")

    # 2. Code Generation Quality
    def test_java_two_sum_generation(self):
        java_spec = LANGUAGES["java"]
        code = coder_engine.generate_code("two sum", java_spec, class_name="TwoSum")
        self.assertIn("public class TwoSum", code)
        self.assertIn("twoSum", code)
        self.assertIn("HashMap", code)
        self.assertIn("public static void main", code)

    def test_python_binary_search_generation(self):
        py_spec = LANGUAGES["python"]
        code = coder_engine.generate_code("binary search", py_spec)
        self.assertIn("def binary_search", code)
        self.assertIn('if __name__ == "__main__":', code)

    def test_cpp_sort_generation(self):
        cpp_spec = LANGUAGES["cpp"]
        code = coder_engine.generate_code("merge sort", cpp_spec, class_name="Solution")
        self.assertIn("#include <iostream>", code)
        self.assertIn("mergeSort", code)

    # 3. Code Execution
    def test_python_local_execution(self):
        py_file = self.test_dir / "test_exec.py"
        py_file.write_text("print('ZYRA_EXECUTION_SUCCESS')")
        res = code_runner.execute_file(str(py_file))
        self.assertTrue(res["success"])
        self.assertIn("ZYRA_EXECUTION_SUCCESS", res["output"])

    # 4. IDE Detection
    def test_ide_detection(self):
        # Notepad is guaranteed on all Windows installations
        notepad_path = ide_manager.get_ide_path("notepad")
        self.assertIsNotNone(notepad_path)
        # VS Code check
        vscode_path = ide_manager.get_ide_path("vscode")
        self.assertIsNotNone(vscode_path)

    # 5. Online Compiler URLs
    def test_online_compiler_mapping(self):
        java_url = online_compiler.get_compiler_url("java")
        self.assertIn("onecompiler.com/java", java_url)
        rust_url = online_compiler.get_compiler_url("rust")
        self.assertIn("rust", rust_url)

    # 6. Coding Coordinator Integration
    def test_coding_intent_detection(self):
        self.assertTrue(coding_coordinator.is_coding_intent("create java file TwoSum and open in vscode"))
        self.assertTrue(coding_coordinator.is_coding_intent("write python code for binary search and run it"))
        self.assertTrue(coding_coordinator.is_coding_intent("open online compiler for C++"))

    def test_end_to_end_coding_execution(self):
        cmd = f"write python code for factorial in {str(self.test_dir)} and run it"
        result = coding_coordinator.execute_coding_task(cmd)
        self.assertIn("Python file", result)
        self.assertIn("Execution Output", result)
        self.assertIn("Factorial", result)

    # 7. Anywhere Path Resolution Tests
    def test_anywhere_path_resolution(self):
        custom_folder = self.test_dir / "my_custom_project"
        cmd = f"create java file TwoSum in {str(custom_folder)}"
        target_dir, fname = coding_coordinator.resolve_file_location(cmd, LANGUAGES["java"])
        self.assertEqual(target_dir, custom_folder.resolve())
        self.assertEqual(fname, "TwoSum.java")

        # Full path specified
        full_path = self.test_dir / "direct" / "Solution.py"
        cmd2 = f"create {str(full_path)} and write code"
        target_dir2, fname2 = coding_coordinator.resolve_file_location(cmd2, LANGUAGES["python"])
        self.assertEqual(target_dir2, full_path.parent.resolve())
        self.assertEqual(fname2, "Solution.py")

        # Smart location without typing path
        cmd3 = "open this folder on vscode create new file on this folder and write code for two sum"
        target_dir3, fname3 = coding_coordinator.resolve_file_location(cmd3, LANGUAGES["java"])
        self.assertIsNotNone(target_dir3)
        self.assertEqual(fname3, "TwoSum.java")

        # Named folder without path
        cmd4 = "open DSA folder on vscode and create new file"
        target_dir4, fname4 = coding_coordinator.resolve_file_location(cmd4, LANGUAGES["java"])
        self.assertTrue(str(target_dir4).endswith("DSA"))
        self.assertEqual(fname4, "Solution.java")

    # 8. Strengthened Voice Normalization
    def test_voice_normalization(self):
        from zyra.voice_manager import normalize_voice_transcript
        self.assertEqual(normalize_voice_transcript("open v s code"), "open vscode")
        self.assertEqual(normalize_voice_transcript("create c plus plus file"), "create cpp file")
        self.assertEqual(normalize_voice_transcript("solve to sum in java"), "solve two sum in java")
        self.assertEqual(normalize_voice_transcript("hey friday open chrome"), "friday open chrome")

    # 9. Autonomous Synthesis (Snake Game, LRU Cache)
    def test_autonomous_game_and_lru_synthesis(self):
        py_spec = LANGUAGES["python"]
        snake_code = coder_engine.generate_code("write snake game in python", py_spec)
        self.assertIn("SnakeGame", snake_code)
        self.assertIn("tkinter", snake_code)

        java_spec = LANGUAGES["java"]
        lru_code = coder_engine.generate_code("lru cache", java_spec, class_name="LRUCache")
        self.assertIn("public class LRUCache", lru_code)
        self.assertIn("get(int key)", lru_code)

if __name__ == "__main__":
    unittest.main()

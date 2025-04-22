import unittest
import os
import tempfile
from datetime import datetime, timedelta
from eod_move_tasks import process_markdown_file
import re

class TestEodMoveTasks(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        self.temp_file_path = self.temp_file.name

    def tearDown(self):
        # Clean up the temporary file
        self.temp_file.close()
        os.unlink(self.temp_file_path)

    def write_test_content(self, content):
        self.temp_file.seek(0)
        self.temp_file.truncate()
        self.temp_file.write(content)
        self.temp_file.flush()

    def read_test_content(self):
        self.temp_file.seek(0)
        return self.temp_file.read()

    def get_section_content(self, content, section_name):
        """Extract content of a specific section from the markdown."""
        pattern = rf'## {section_name}\s*(.*?)(?=^## |\Z)'
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        return match.group(1).strip() if match else ""

    def print_file_contents(self):
        """Print the current contents of the test file."""
        print("\nCurrent file contents:")
        print("-" * 80)
        print(self.read_test_content())
        print("-" * 80)

    def assertIn(self, member, container, msg=None):
        """Override assertIn to print file contents on failure."""
        try:
            super().assertIn(member, container, msg)
        except AssertionError:
            self.print_file_contents()
            raise

    def assertNotIn(self, member, container, msg=None):
        """Override assertNotIn to print file contents on failure."""
        try:
            super().assertNotIn(member, container, msg)
        except AssertionError:
            self.print_file_contents()
            raise

    def assertEqual(self, first, second, msg=None):
        """Override assertEqual to print file contents on failure."""
        try:
            super().assertEqual(first, second, msg)
        except AssertionError:
            self.print_file_contents()
            raise

    def assertFalse(self, expr, msg=None):
        """Override assertFalse to print file contents on failure."""
        try:
            super().assertFalse(expr, msg)
        except AssertionError:
            self.print_file_contents()
            raise

    def test_completed_tasks_moved(self):
        test_content = """## Today
- [x] Completed task 1
- [ ] Uncompleted task 1

## Tonight
- [x] Completed task 2
- [ ] Uncompleted task 2

## Completed"""
        
        self.write_test_content(test_content)
        process_markdown_file(self.temp_file_path)
        
        content = self.read_test_content()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")
        
        # Get content of each section
        today_content = self.get_section_content(content, "Today")
        tonight_content = self.get_section_content(content, "Tonight")
        completed_content = self.get_section_content(content, "Completed")
        
        # Check original sections
        self.assertNotIn("- [x] Completed task 1", today_content)
        self.assertIn("- [ ] > Uncompleted task 1", today_content)
        self.assertNotIn("- [x] Completed task 2", tonight_content)
        self.assertIn("- [ ] > Uncompleted task 2", tonight_content)
        
        # Check completed section
        self.assertIn(f"### {yesterday}", completed_content)
        self.assertIn("- [x] Completed task 1", completed_content)
        self.assertIn("- [x] Completed task 2", completed_content)

    def test_uncompleted_tasks_marked(self):
        test_content = """## Today
- [ ] Task 1
- [ ] > Task 2
- [ ] >> Task 3

## Tonight
- [ ] Task 4"""
        
        self.write_test_content(test_content)
        process_markdown_file(self.temp_file_path)
        
        content = self.read_test_content()
        
        # Get content of each section
        today_content = self.get_section_content(content, "Today")
        tonight_content = self.get_section_content(content, "Tonight")
        
        # Check that uncompleted tasks were marked
        self.assertIn("- [ ] > Task 1", today_content)
        self.assertIn("- [ ] >> Task 2", today_content)
        self.assertIn("- [ ] >>> Task 3", today_content)
        self.assertIn("- [ ] > Task 4", tonight_content)

    def test_multiple_days_accumulation(self):
        test_content = """## Today
- [ ] > Task 1
- [ ] >> Task 2"""
        
        self.write_test_content(test_content)
        
        # Process multiple days
        for _ in range(3):
            process_markdown_file(self.temp_file_path)
            self.write_test_content(self.read_test_content())
        
        content = self.read_test_content()
        today_content = self.get_section_content(content, "Today")
        
        # Check that '>' markers accumulated correctly
        self.assertIn("- [ ] >>>> Task 1", today_content)
        self.assertIn("- [ ] >>>>> Task 2", today_content)

    def test_empty_sections(self):
        test_content = """## Today

## Tonight

## Completed"""
        
        self.write_test_content(test_content)
        process_markdown_file(self.temp_file_path)
        
        content = self.read_test_content()
        
        # Get content of each section
        today_content = self.get_section_content(content, "Today")
        tonight_content = self.get_section_content(content, "Tonight")
        completed_content = self.get_section_content(content, "Completed")
        
        # Check that sections are empty
        self.assertEqual(today_content, "")
        self.assertEqual(tonight_content, "")
        self.assertEqual(completed_content, "")

    def test_no_blank_lines_at_top(self):
        test_content = """## Today
- [ ] Task 1
- [x] Task 2

## Tonight
- [ ] Task 3"""
        
        self.write_test_content(test_content)
        process_markdown_file(self.temp_file_path)
        
        content = self.read_test_content()
        
        # Get content of each section
        today_content = self.get_section_content(content, "Today")
        tonight_content = self.get_section_content(content, "Tonight")
        
        # Check that there are no blank lines after section headers
        self.assertFalse(today_content.startswith("\n"))
        self.assertFalse(tonight_content.startswith("\n"))

    def test_missing_completed_section(self):
        test_content = """## Today
- [x] Completed task 1
- [ ] Uncompleted task 1

## Tonight
- [x] Completed task 2"""
        
        self.write_test_content(test_content)
        process_markdown_file(self.temp_file_path)
        
        content = self.read_test_content()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")
        
        # Get content of each section
        today_content = self.get_section_content(content, "Today")
        tonight_content = self.get_section_content(content, "Tonight")
        completed_content = self.get_section_content(content, "Completed")
        
        # Check original sections
        self.assertNotIn("- [x] Completed task 1", today_content)
        self.assertIn("- [ ] > Uncompleted task 1", today_content)
        self.assertNotIn("- [x] Completed task 2", tonight_content)
        
        # Check completed section was created
        self.assertIn(f"### {yesterday}", completed_content)
        self.assertIn("- [x] Completed task 1", completed_content)
        self.assertIn("- [x] Completed task 2", completed_content)

    def test_existing_yesterday_section(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")
        test_content = f"""## Today
- [x] Completed task 1
- [ ] Uncompleted task 1

## Tonight
- [x] Completed task 2

## Completed
### {yesterday}
- [x] Old completed task"""
        
        self.write_test_content(test_content)
        process_markdown_file(self.temp_file_path)
        
        content = self.read_test_content()
        
        # Get content of each section
        today_content = self.get_section_content(content, "Today")
        tonight_content = self.get_section_content(content, "Tonight")
        completed_content = self.get_section_content(content, "Completed")
        
        # Check original sections
        self.assertNotIn("- [x] Completed task 1", today_content)
        self.assertIn("- [ ] > Uncompleted task 1", today_content)
        self.assertNotIn("- [x] Completed task 2", tonight_content)
        
        # Check completed section - should only have one yesterday section
        yesterday_sections = completed_content.count(f"### {yesterday}")
        self.assertEqual(yesterday_sections, 1)
        self.assertIn("- [x] Old completed task", completed_content)
        self.assertIn("- [x] Completed task 1", completed_content)
        self.assertIn("- [x] Completed task 2", completed_content)

if __name__ == '__main__':
    unittest.main() 
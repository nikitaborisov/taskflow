from __future__ import annotations
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

    def test_completed_section_newlines(self):
        """Regression test to verify proper newline handling between sections in the Completed section."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")
        two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%B %d, %Y")
        
        test_content = f"""## Today
- [x] New completed task 1
- [ ] Uncompleted task

## Tonight
- [x] New completed task 2

## Completed
### {two_days_ago}
- [x] Old task 1
- [x] Old task 2"""
        
        self.write_test_content(test_content)
        process_markdown_file(self.temp_file_path)
        
        content = self.read_test_content()
        
        # Get the Completed section content
        completed_content = self.get_section_content(content, "Completed")
        
        # Split the content into lines for analysis
        lines = completed_content.split('\n')
        
        # Find the indices of section headers
        header_indices = [i for i, line in enumerate(lines) if line.startswith('###')]
        
        # Verify there's exactly one newline between sections
        for i in range(len(header_indices) - 1):
            # Get the lines between this header and the next
            section_lines = lines[header_indices[i]:header_indices[i + 1]]
            # Count empty lines at the end of the section
            empty_lines_at_end = 0
            for line in reversed(section_lines):
                if line.strip() == '':
                    empty_lines_at_end += 1
                else:
                    break
            self.assertEqual(empty_lines_at_end, 0, 
                           f"Found {empty_lines_at_end} empty lines between sections instead of 0")
        
        # Verify the content has the expected format (new tasks at the end)
        expected_pattern = f"""### {two_days_ago}
- [x] Old task 1
- [x] Old task 2
### {yesterday}
- [x] New completed task 1
- [x] New completed task 2"""
        
        self.assertEqual(completed_content.strip(), expected_pattern)

    def test_subtask_handling(self):
        """Test that completed subtasks are moved to Completed section while preserving parent task."""
        test_content = """## Today
- [ ] ! Hotels for +flaz25 trip
  - [x] GNV
  - [ ] TPA
  - [ ] PHX

- [ ] ! Another task
  - [x] Subtask 1
  - [x] Subtask 2
  - [ ] Subtask 3

## Completed"""
        
        self.write_test_content(test_content)
        process_markdown_file(self.temp_file_path)
        
        content = self.read_test_content()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")
        
        # Get content of each section
        today_content = self.get_section_content(content, "Today")
        completed_content = self.get_section_content(content, "Completed")
        
        # Check Today section
        self.assertIn("- [ ] > ! Hotels for +flaz25 trip", today_content)
        self.assertIn("  - [ ] TPA", today_content)
        self.assertIn("  - [ ] PHX", today_content)
        self.assertNotIn("  - [x] GNV", today_content)
        
        self.assertIn("- [ ] > ! Another task", today_content)
        self.assertIn("  - [ ] Subtask 3", today_content)
        self.assertNotIn("  - [x] Subtask 1", today_content)
        self.assertNotIn("  - [x] Subtask 2", today_content)
        
        # Check Completed section
        self.assertIn(f"### {yesterday}", completed_content)
        self.assertIn("- [ ] ! Hotels for +flaz25 trip", completed_content)
        self.assertIn("  - [x] GNV", completed_content)
        self.assertIn("- [ ] ! Another task", completed_content)
        self.assertIn("  - [x] Subtask 1", completed_content)
        self.assertIn("  - [x] Subtask 2", completed_content)

    def test_completed_parent_task(self):
        """Test that a completed parent task with all completed subtasks is fully moved to Completed."""
        test_content = """## Today
- [x] ! Fully completed task
  - [x] Subtask 1
  - [x] Subtask 2

- [ ] ! Incomplete task
  - [x] Subtask 1
  - [ ] Subtask 2

## Completed"""
        
        self.write_test_content(test_content)
        process_markdown_file(self.temp_file_path)
        
        content = self.read_test_content()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")
        
        # Get content of each section
        today_content = self.get_section_content(content, "Today")
        completed_content = self.get_section_content(content, "Completed")
        
        # Check Today section
        self.assertNotIn("- [x] ! Fully completed task", today_content)
        self.assertIn("- [ ] > ! Incomplete task", today_content)
        self.assertIn("  - [ ] Subtask 2", today_content)
        self.assertNotIn("  - [x] Subtask 1", today_content)
        
        # Check Completed section
        self.assertIn(f"### {yesterday}", completed_content)
        self.assertIn("- [x] ! Fully completed task", completed_content)
        self.assertIn("  - [x] Subtask 1", completed_content)
        self.assertIn("  - [x] Subtask 2", completed_content)
        self.assertIn("- [ ] ! Incomplete task", completed_content)
        self.assertIn("  - [x] Subtask 1", completed_content)

    def test_multiple_days_subtask_progress(self):
        """Test that subtask progress is tracked correctly over multiple days."""
        test_content = """## Today
- [ ] > ! Hotels for +flaz25 trip
  - [x] GNV
  - [ ] TPA
  - [ ] PHX

## Completed
### Yesterday
- [ ] ! Hotels for +flaz25 trip
  - [x] GNV"""
        
        self.write_test_content(test_content)
        process_markdown_file(self.temp_file_path)
        
        content = self.read_test_content()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")
        
        # Get content of each section
        today_content = self.get_section_content(content, "Today")
        completed_content = self.get_section_content(content, "Completed")
        
        # Check Today section
        self.assertIn("- [ ] >> ! Hotels for +flaz25 trip", today_content)
        self.assertIn("  - [ ] TPA", today_content)
        self.assertIn("  - [ ] PHX", today_content)
        self.assertNotIn("  - [x] GNV", today_content)
        
        # Check Completed section
        self.assertIn(f"### {yesterday}", completed_content)
        self.assertIn("- [ ] ! Hotels for +flaz25 trip", completed_content)
        self.assertIn("  - [x] GNV", completed_content)

    def test_subtask_indentation(self):
        """Test that subtask indentation is preserved correctly."""
        test_content = """## Today
- [ ] ! Task with nested subtasks
  - [x] Level 1
    - [x] Level 2
      - [x] Level 3
  - [ ] Uncompleted

## Completed"""
        
        self.write_test_content(test_content)
        process_markdown_file(self.temp_file_path)
        
        content = self.read_test_content()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")
        
        # Get content of each section
        today_content = self.get_section_content(content, "Today")
        completed_content = self.get_section_content(content, "Completed")
        
        # Check Today section
        self.assertIn("- [ ] > ! Task with nested subtasks", today_content)
        self.assertIn("  - [ ] Uncompleted", today_content)
        
        # Check Completed section
        self.assertIn(f"### {yesterday}", completed_content)
        self.assertIn("- [ ] ! Task with nested subtasks", completed_content)
        self.assertIn("  - [x] Level 1", completed_content)
        self.assertIn("    - [x] Level 2", completed_content)
        self.assertIn("      - [x] Level 3", completed_content)


if __name__ == '__main__':
    unittest.main() 
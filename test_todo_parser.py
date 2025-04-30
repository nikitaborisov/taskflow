import unittest
from todo_parser import Task, Section, TodoParser
import pytest
from hypothesis import given, strategies as st

class TestTodoParser(unittest.TestCase):
    def setUp(self):
        self.parser = TodoParser()

    def print_sections(self, sections: list[Section], indent: int = 0) -> None:
        """Helper method to print the parsed structure."""
        indent_str = "  " * indent
        for section in sections:
            print(f"{indent_str}Section: {section.title}")
            if section.tasks:
                print(f"{indent_str}Tasks:")
                self.print_tasks(section.tasks, indent + 1)
            if section.subsections:
                print(f"{indent_str}Subsections:")
                self.print_sections(section.subsections, indent + 1)

    def print_tasks(self, tasks: list[Task], indent: int = 0) -> None:
        """Helper method to print tasks and their subtasks."""
        indent_str = "  " * indent
        for task in tasks:
            status = "[x]" if task.is_completed else "[ ]"
            procrastination = ">" * task.procrastination_level
            print(f"{indent_str}{status} {procrastination} {task.content} (indent: {task.indent_level})")
            if task.subtasks:
                self.print_tasks(task.subtasks, indent + 1)

    def test_parse_basic_sections(self):
        content = """## Today
- [ ] Task 1

## Tonight
- [x] Task 2
"""
        sections = self.parser.parse_file(content)
        try:
            self.assertEqual(len(sections), 2)
            self.assertEqual(sections[0].title, "Today")
            self.assertEqual(sections[1].title, "Tonight")
            self.assertEqual(sections[0].tasks[0].content, "Task 1")
            self.assertEqual(sections[1].tasks[0].content, "Task 2")
            self.assertEqual(sections[0].tasks[0].procrastination_level, 0)
            self.assertEqual(sections[1].tasks[0].procrastination_level, 0)
            self.assertEqual(sections[0].tasks[0].indent_level, 0)
            self.assertEqual(sections[1].tasks[0].indent_level, 0)
            self.assertFalse(sections[0].tasks[0].is_completed)
            self.assertTrue(sections[1].tasks[0].is_completed)
        except AssertionError:
            print("\nParsed structure:")
            self.print_sections(sections)
            raise

    def test_parse_subsections(self):
        content = """## Today
### Morning
- [x] Morning task

### Evening
- [ ] Evening task
"""
        sections = self.parser.parse_file(content)
        try:
            self.assertEqual(len(sections), 1)
            self.assertEqual(len(sections[0].subsections), 2)
            self.assertEqual(sections[0].subsections[0].title, "Morning")
            self.assertEqual(sections[0].subsections[1].title, "Evening")
            self.assertEqual(sections[0].subsections[0].tasks[0].content, "Morning task")
            self.assertTrue(sections[0].subsections[0].tasks[0].is_completed)
            self.assertEqual(sections[0].subsections[1].tasks[0].content, "Evening task")
            self.assertFalse(sections[0].subsections[1].tasks[0].is_completed)  
        except AssertionError:
            print("\nParsed structure:")
            self.print_sections(sections)
            raise

    def test_parse_tasks(self):
        content = """## Today
- [ ] Task 1
- [x] Completed task
- [ ] > Procrastinated task
- [ ] >> Very procrastinated task
"""
        sections = self.parser.parse_file(content)
        try:
            self.assertEqual(len(sections[0].tasks), 4)
            
            # Check task 1
            self.assertEqual(sections[0].tasks[0].content, "Task 1")
            self.assertFalse(sections[0].tasks[0].is_completed)
            self.assertEqual(sections[0].tasks[0].procrastination_level, 0)
            
            # Check completed task
            self.assertEqual(sections[0].tasks[1].content, "Completed task")
            self.assertTrue(sections[0].tasks[1].is_completed)
            
            # Check procrastinated tasks
            self.assertEqual(sections[0].tasks[2].content, "Procrastinated task")
            self.assertEqual(sections[0].tasks[2].procrastination_level, 1)
            
            self.assertEqual(sections[0].tasks[3].content, "Very procrastinated task")
            self.assertEqual(sections[0].tasks[3].procrastination_level, 2)
        except AssertionError:
            print("\nParsed structure:")
            self.print_sections(sections)
            raise

    def test_parse_subtasks(self):
        content = """## Today
- [ ] Parent task
  - [ ] Subtask 1
  - [x] Completed subtask
    - [ ] Nested subtask
"""
        sections = self.parser.parse_file(content)
        try:
            self.assertEqual(len(sections[0].tasks), 1)
            parent_task = sections[0].tasks[0]
            
            self.assertEqual(parent_task.content, "Parent task")
            self.assertEqual(len(parent_task.subtasks), 2)
            
            # Check subtasks
            self.assertEqual(parent_task.subtasks[0].content, "Subtask 1")
            self.assertFalse(parent_task.subtasks[0].is_completed)
            
            self.assertEqual(parent_task.subtasks[1].content, "Completed subtask")
            self.assertTrue(parent_task.subtasks[1].is_completed)
            
            # Check nested subtask
            self.assertEqual(len(parent_task.subtasks[1].subtasks), 1)
            self.assertEqual(parent_task.subtasks[1].subtasks[0].content, "Nested subtask")
        except AssertionError:
            print("\nParsed structure:")
            self.print_sections(sections)
            raise

    def test_parse_complex_structure(self):
        content = """## Today
### Morning
- [ ] Morning task 1
- [ ] > Procrastinated morning task
  - [ ] Morning subtask

### Evening
- [x] Completed evening task
- [ ] Evening task 2
  - [x] Completed subtask
    - [ ] >> Very procrastinated nested task

## Completed
### Yesterday
- [x] Completed task from yesterday
"""
        sections = self.parser.parse_file(content)
        try:
            # Check Today section
            self.assertEqual(len(sections[0].subsections), 2)
            
            # Check Morning subsection
            morning_tasks = sections[0].subsections[0].tasks
            self.assertEqual(len(morning_tasks), 2)
            self.assertEqual(morning_tasks[1].procrastination_level, 1)
            self.assertEqual(len(morning_tasks[1].subtasks), 1)
            
            # Check Evening subsection
            evening_tasks = sections[0].subsections[1].tasks
            self.assertEqual(len(evening_tasks), 2)
            self.assertTrue(evening_tasks[0].is_completed)
            self.assertEqual(evening_tasks[1].subtasks[0].subtasks[0].procrastination_level, 2)
            
            # Check Completed section
            self.assertEqual(sections[1].title, "Completed")
            self.assertEqual(sections[1].subsections[0].title, "Yesterday")
        except AssertionError:
            print("\nParsed structure:")
            self.print_sections(sections)
            raise

# Helper functions for generating test data
def generate_markdown_section(level: int, title: str) -> str:
    return f"{'#' * level} {title}\n"

def generate_markdown_task(indent: int, completed: bool, procrastination: int, content: str) -> str:
    indent_str = '  ' * indent
    status = 'x' if completed else ' '
    procrastination_str = f" {'>' * procrastination} " if procrastination > 0 else " "
    return f"{indent_str}- [{status}]{procrastination_str}{content}\n"

# Property-based test strategies
def valid_section_title() -> st.SearchStrategy[str]:
    return st.text(
        alphabet=st.characters(blacklist_characters='#\n'),
        min_size=1
    ).map(lambda s: s.strip()).filter(lambda s: len(s) > 0)  # Ensure non-empty after stripping

def valid_task_content() -> st.SearchStrategy[str]:
    return st.text(
        alphabet=st.characters(blacklist_characters='[]\n', blacklist_categories=('Cc',)),  # Exclude control characters
        min_size=1
    ).map(lambda s: s.strip())  # Strip whitespace from generated content

def valid_section_level() -> st.SearchStrategy[int]:
    return st.integers(min_value=1, max_value=6)  # Markdown supports h1-h6

def valid_indent_level() -> st.SearchStrategy[int]:
    return st.integers(min_value=0, max_value=5)  # Reasonable nesting depth

def valid_procrastination_level() -> st.SearchStrategy[int]:
    return st.integers(min_value=0, max_value=3)  # Reasonable procrastination levels

def generate_valid_task_sequence() -> st.SearchStrategy[list[tuple[str, int, bool, int]]]:
    """Generate a sequence of tasks with valid indentation levels."""
    return st.lists(
        st.tuples(
            valid_task_content(),
            st.integers(min_value=0, max_value=3),  # Limit max indentation
            st.booleans(),
            valid_procrastination_level()
        ),
        min_size=1,
        max_size=10
    ).filter(lambda tasks: 
        # First task must be top-level
        tasks[0][1] == 0 and
        # Each subsequent task's indent level must be <= previous level + 1
        all(tasks[i][1] <= tasks[i-1][1] + 1 for i in range(1, len(tasks)))
    )

# Test properties
@given(
    title=valid_section_title(),
    level=valid_section_level()
)
def test_section_parsing_properties(title: str, level: int):
    """Test that section parsing maintains certain properties."""
    parser = TodoParser()
    markdown = generate_markdown_section(level, title)
    sections = parser.parse_file(markdown)
    
    # Property 1: Single section should be created
    assert len(sections) == 1
    
    # Property 2: Section title should match input (stripped)
    assert sections[0].title == title.strip()
    
    # Property 3: Section level should match input
    assert sections[0].level == level
    
    # Property 4: Section should have no parent
    assert sections[0].parent is None
    
    # Property 5: Section should have no subsections
    assert len(sections[0].subsections) == 0
    
    # Property 6: Section should have no tasks
    assert len(sections[0].tasks) == 0

@given(
    content=valid_task_content(),
    completed=st.booleans(),
    procrastination=valid_procrastination_level()
)
def test_task_parsing_properties(content: str, completed: bool, procrastination: int):
    """Test that task parsing maintains certain properties."""
    parser = TodoParser()
    # Create a section to contain the task
    markdown = generate_markdown_section(1, "Test Section")
    markdown += generate_markdown_task(0, completed, procrastination, content)  # Always use indent_level=0
    sections = parser.parse_file(markdown)
    
    # Property 1: Section should contain exactly one task
    assert len(sections[0].tasks) == 1
    
    task = sections[0].tasks[0]
    
    # Property 2: Task content should match input (stripped)
    assert task.content == content.strip()
    
    # Property 3: Task completion status should match input
    assert task.is_completed == completed
    
    # Property 4: Task indent level should be 0
    assert task.indent_level == 0
    
    # Property 5: Task procrastination level should match input
    assert task.procrastination_level == procrastination
    
    # Property 6: Task should have no subtasks
    assert len(task.subtasks) == 0
    
    # Property 7: Task should have no parent
    assert task.parent is None

@given(
    sections=st.lists(
        st.tuples(
            valid_section_title(),
            valid_section_level()
        ),
        min_size=1,
        max_size=5
    ).filter(lambda lst: lst[0][1] == min(level for _, level in lst))  # First section must have minimal level
)
def test_section_hierarchy_properties(sections: list[tuple[str, int]]):
    """Test that section hierarchy maintains certain properties."""
    parser = TodoParser()
    markdown = ""
    for title, level in sections:
        markdown += generate_markdown_section(level, title)
    
    parsed_sections = parser.parse_file(markdown)
    
    # Property 1: Number of root sections should match number of sections with minimal level
    min_level = min(level for _, level in sections)
    expected_root_sections = sum(1 for _, level in sections if level == min_level)
    assert len(parsed_sections) == expected_root_sections
    
    # Property 2: Section levels should be valid
    def validate_section_levels(section: Section):
        assert 1 <= section.level <= 6
        for subsection in section.subsections:
            assert subsection.level > section.level
            validate_section_levels(subsection)
    
    for section in parsed_sections:
        validate_section_levels(section)
    
    # Property 3: Parent-child relationships should be correct
    def validate_parent_relationships(section: Section):
        for subsection in section.subsections:
            assert subsection.parent == section
            validate_parent_relationships(subsection)
    
    for section in parsed_sections:
        validate_parent_relationships(section)

@given(tasks=generate_valid_task_sequence())
def test_task_hierarchy_properties(tasks: list[tuple[str, int, bool, int]]):
    """Test that task hierarchy maintains certain properties."""
    parser = TodoParser()
    markdown = generate_markdown_section(1, "Test Section")
    for content, indent, completed, procrastination in tasks:
        markdown += generate_markdown_task(indent, completed, procrastination, content)
    
    sections = parser.parse_file(markdown)
    
    # Property 1: All tasks should be properly nested
    def validate_task_hierarchy(task: Task):
        for subtask in task.subtasks:
            assert subtask.indent_level > task.indent_level
            assert subtask.parent == task
            validate_task_hierarchy(subtask)
    
    for task in sections[0].tasks:
        validate_task_hierarchy(task)
    
    # Property 2: Indent levels should be consistent
    def validate_indent_levels(task: Task):
        for subtask in task.subtasks:
            assert subtask.indent_level == task.indent_level + 1
            validate_indent_levels(subtask)
    
    for task in sections[0].tasks:
        validate_indent_levels(task)

def assert_sections_equal(section1: Section, section2: Section) -> None:
    """Recursively assert that two sections and their contents are equal."""
    # Check section properties
    assert section1.title == section2.title
    assert section1.level == section2.level
    
    # Check tasks
    assert len(section1.tasks) == len(section2.tasks)
    for task1, task2 in zip(section1.tasks, section2.tasks):
        assert_tasks_equal(task1, task2)
    
    # Check subsections
    assert len(section1.subsections) == len(section2.subsections)
    for sub1, sub2 in zip(section1.subsections, section2.subsections):
        assert_sections_equal(sub1, sub2)

def assert_tasks_equal(task1: Task, task2: Task) -> None:
    """Recursively assert that two tasks and their subtasks are equal."""
    # Check task properties
    assert task1.content == task2.content
    assert task1.is_completed == task2.is_completed
    assert task1.procrastination_level == task2.procrastination_level
    assert task1.indent_level == task2.indent_level
    
    # Check subtasks
    assert len(task1.subtasks) == len(task2.subtasks)
    for subtask1, subtask2 in zip(task1.subtasks, task2.subtasks):
        assert_tasks_equal(subtask1, subtask2)

def test_to_markdown():
    """Test that to_markdown produces valid markdown that can be parsed back."""
    parser = TodoParser()
    
    # Test basic structure
    content = """# Today
- [ ] Buy groceries
- [x] Call mom
- [ ] > Clean the house
  - [ ] Vacuum
  - [ ] Dust

## Work
- [ ] Check emails
- [ ] >> Write documentation
  - [ ] API docs
"""
    
    # Parse and then convert back to markdown
    sections = parser.parse_file(content)
    markdown = parser.to_markdown(sections)
    
    # Parse the generated markdown
    new_sections = parser.parse_file(markdown)
    
    # The two section lists should be equivalent
    assert len(sections) == len(new_sections)
    for section, new_section in zip(sections, new_sections):
        assert_sections_equal(section, new_section)

if __name__ == '__main__':
    unittest.main() 
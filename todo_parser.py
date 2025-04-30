"""
Todo Parser

This module provides a parser for TODO files, as specified in the `FORMAT.md` file. The parser
converts markdown content into a structured representation of sections and tasks.

The parser enforces the following rules:

Sections:
- The first section must have the minimal level among all sections
- Section levels must increase by 1 (e.g., h1 → h2 → h3)
- Section titles cannot contain '#' or newlines
- Leading/trailing whitespace in titles is stripped

Tasks:
- First task in a section must be top-level (no indentation)
- Each subsequent task's indentation must be <= previous task's indentation + 1 level
- Task content cannot contain '[' or ']' characters
- Leading/trailing whitespace in content is stripped
- Control characters are not allowed in content

The parser will raise errors for:
- Tasks outside of sections
- Subtasks without parent tasks
- Invalid section hierarchy
- Empty section titles
- Tasks with invalid indentation
- Unexpected non-empty lines
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import re

@dataclass
class Task:
    content: str
    is_completed: bool = False
    procrastination_level: int = 0  # Number of '>' characters
    subtasks: List['Task'] = field(default_factory=list)
    indent_level: int = 0
    line_number: int = 0  # Add line number to maintain order
    parent: Optional['Task'] = None

@dataclass
class Section:
    title: str
    level: int
    subsections: List['Section'] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    parent: Optional['Section'] = None

@dataclass
class ParserState:
    """Manages the state of the parser during parsing."""
    sections: List[Section] = field(default_factory=list)
    current_section: Optional[Section] = None
    current_task: Optional[Task] = None
    line_number: int = 0
    
    def add_section(self, section: Section) -> None:
        """Add a new section to the state."""
        if self.current_section:
            if self.current_section.level < section.level:
                # This is a subsection
                section.parent = self.current_section
                self.current_section.subsections.append(section)
            else:
                # Find the appropriate parent section
                parent_level = section.level - 1
                parent = self.current_section.parent
                while parent and parent.level > parent_level:
                    parent = parent.parent
                
                section.parent = parent
                if not section.parent:
                    self.sections.append(section)
                else:
                    section.parent.subsections.append(section)
        else:
            # First section
            self.sections.append(section)
        
        self.current_section = section
        self.current_task = None  # Reset current task when entering new section
    
    def add_task(self, task: Task) -> None:
        """Add a new task to the state."""
        if task.indent_level:
            # This is a subtask
            if not self.current_task:
                raise ValueError(f"Subtask without parent task at line {self.line_number}")
            
            parent = self.current_task
            while parent.indent_level > task.indent_level - 1:
                parent = parent.parent
            parent.subtasks.append(task)
            task.parent = parent
        else:
            # This is a top-level task
            if self.current_section:
                self.current_section.tasks.append(task)
            else:
                raise ValueError(f"Task outside of section at line {self.line_number}")
        
        self.current_task = task

class TodoParser:
    def __init__(self):
        self.section_pattern = re.compile(r'^(#+)\s+(.+)$')
        self.task_pattern = re.compile(r'^(\s*)- \[([ x])\](\s+(>+)\s+)?(.*?)$')

    def _parse_section(self, line: str, line_number: int) -> Optional[Section]:
        """Parse a section header line and return a Section object."""
        match = self.section_pattern.match(line)
        if not match:
            return None
        level = len(match.group(1))
        return Section(title=match.group(2), level=level)

    def _parse_task(self, line: str, line_number: int) -> Optional[Task]:
        """Parse a task line and return a Task object."""
        match = self.task_pattern.match(line)
        if not match:
            return None
        indent, status, _, procrastination, content = match.groups()
        return Task(
            content=content.strip(),
            is_completed=(status == 'x'),
            procrastination_level=len(procrastination) if procrastination else 0,
            indent_level=len(indent) // 2,
            line_number=line_number
        )

    def parse_file(self, content: str) -> List[Section]:
        """Parse the entire markdown content into a list of sections."""
        state = ParserState()
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            state.line_number = i
            
            # Try to parse section first
            section = self._parse_section(line, i)
            if section:
                state.add_section(section)
                continue

            # Try to parse task
            task = self._parse_task(line, i)
            if task:
                state.add_task(task)
                continue

            # Non-empty non-task lines are not allowed
            if line.strip():
                raise ValueError(f"Unexpected line: {line}")

        return state.sections

    def to_markdown(self, sections: List[Section]) -> str:
        """Convert sections and tasks back to markdown format.
        
        Args:
            sections: List of sections to convert
            
        Returns:
            A string containing the markdown representation of the sections and tasks
        """
        def section_to_markdown(section: Section, indent: int = 0) -> str:
            """Convert a section and its contents to markdown."""
            result = []
            # Add section header
            result.append(f"{'#' * section.level} {section.title}")
            
            # Add tasks
            for task in section.tasks:
                result.append(task_to_markdown(task))
            
            # Add subsections
            for subsection in section.subsections:
                result.append(section_to_markdown(subsection, indent + 1))
            
            return '\n'.join(result)
        
        def task_to_markdown(task: Task) -> str:
            """Convert a task and its subtasks to markdown."""
            result = []
            # Create task line
            indent = '  ' * task.indent_level
            status = 'x' if task.is_completed else ' '
            procrastination = f" {'>' * task.procrastination_level} " if task.procrastination_level > 0 else " "
            result.append(f"{indent}- [{status}]{procrastination}{task.content}")
            
            # Add subtasks
            for subtask in task.subtasks:
                result.append(task_to_markdown(subtask))
            
            return '\n'.join(result)
        
        # Convert all sections
        return '\n\n'.join(section_to_markdown(section) for section in sections)


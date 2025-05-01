import sys
import argparse
from datetime import datetime, timedelta
from todo_parser import TodoParser, Section, Task

def process_tasks(section: Section) -> tuple[Section, list[Task]]:
    """
    Process a section's tasks to extract completed items and mark uncompleted ones.
    
    Args:
        section: The section to process
        
    Returns:
        tuple: (new_section, completed_tasks) where new_section is the processed section
               and completed_tasks is a list of completed tasks
    """
    completed_tasks = []
    new_tasks = []
    
    for task in section.tasks:
        if task.is_completed or (task.subtasks and all(subtask.is_completed for subtask in task.subtasks)):
            # If the task is completed or all subtasks are completed, move everything to completed
            completed_tasks.append(task)
        else:
            # For tasks with some completed subtasks or uncompleted tasks
            completed_subtasks = []
            remaining_subtasks = []
            
            for subtask in task.subtasks:
                if subtask.is_completed:
                    completed_subtasks.append(subtask)
                else:
                    remaining_subtasks.append(subtask)
            
            if completed_subtasks:
                # Create a copy of the task with only completed subtasks
                completed_task = Task(
                    content=task.content,
                    is_completed=task.is_completed,
                    procrastination_level=task.procrastination_level,
                    indent_level=task.indent_level,
                    subtasks=completed_subtasks
                )
                completed_tasks.append(completed_task)
            
            # Update the task's procrastination level if it's not completed
            if not task.is_completed:
                task.procrastination_level += 1
            
            # Update the task's subtasks to only include remaining ones
            task.subtasks = remaining_subtasks
            new_tasks.append(task)
    
    # Create a new section with the processed tasks
    new_section = Section(
        title=section.title,
        level=section.level,
        tasks=new_tasks,
        subsections=section.subsections
    )
    
    return new_section, completed_tasks

def process_sections(sections: list[Section]) -> tuple[list[Section], int]:
    """
    Process sections to move completed tasks to the Completed section.
    
    Args:
        sections: List of sections to process
        
    Returns:
        tuple: (new_sections, completed_count) where new_sections is the processed sections
               and completed_count is the number of completed items moved
    """
    # Get yesterday's date formatted as "Month Day, Year"
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")
    
    # Process Today and Tonight sections and collect completed items
    completed_tasks = []
    new_sections = []
    
    for section in sections:
        if section.title in ['Today', 'Tonight']:
            new_section, completed = process_tasks(section)
            completed_tasks.extend(completed)
            new_sections.append(new_section)
        else:
            new_sections.append(section)

    # If there are completed items, handle the Completed section
    if completed_tasks:
        # Find or create Completed section
        completed_section = None
        for i, section in enumerate(new_sections):
            if section.title == 'Completed':
                completed_section = (i, section)
                break

        if completed_section:
            # Merge with existing completed section
            i, existing_section = completed_section
            
            # Find yesterday's subsection
            yesterday_subsection = None
            for subsection in existing_section.subsections:
                if subsection.title == yesterday:
                    yesterday_subsection = subsection
                    break
            
            if yesterday_subsection:
                # Add new tasks to existing yesterday subsection
                yesterday_subsection.tasks.extend(completed_tasks)
            else:
                # Create new yesterday subsection
                yesterday_subsection = Section(
                    title=yesterday,
                    level=3,  # h3 for date subsections
                    tasks=completed_tasks
                )
                existing_section.subsections.append(yesterday_subsection)
            
            new_sections[i] = existing_section
        else:
            # Create new completed section with yesterday subsection
            yesterday_subsection = Section(
                title=yesterday,
                level=3,
                tasks=completed_tasks
            )
            completed_section = Section(
                title='Completed',
                level=2,  # h2 for main sections
                subsections=[yesterday_subsection]
            )
            new_sections.append(completed_section)

    return new_sections, len(completed_tasks)

def process_markdown_file(input_path: str, output_path: str = None) -> int:
    """
    Process a markdown file to move completed tasks to the Completed section.
    
    Args:
        input_path: Path to input file or '-' for stdin
        output_path: Path to output file or '-' for stdout. If None, same as input_path.
        
    Returns:
        int: Number of completed items moved
    """
    # Read input
    if input_path == '-':
        content = sys.stdin.read()
    else:
        with open(input_path, 'r') as file:
            content = file.read()

    # Parse the content
    parser = TodoParser()
    sections = parser.parse_file(content)
    
    # Process sections
    new_sections, completed_count = process_sections(sections)

    # Convert back to markdown
    new_content = parser.to_markdown(new_sections)

    if not output_path:
        output_path = input_path

    # Write output
    if output_path == '-':
        sys.stdout.write(new_content)
    else:
        with open(output_path, 'w') as file:
            file.write(new_content)

    return completed_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process markdown tasks and move completed items to Completed section.')
    parser.add_argument('input', help='Input file path (use - for stdin)')
    parser.add_argument('output', nargs='?', help='Output file path (use - for stdout, defaults to input file)')
    args = parser.parse_args()
    
    output_path = args.output if args.output is not None else args.input
    completed_count = process_markdown_file(args.input, output_path)
    print(f"Moved {completed_count} completed items to the 'Completed' section.", file=sys.stderr)

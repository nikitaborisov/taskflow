import re
from datetime import datetime, timedelta
import sys
import argparse

def split_into_sections(content, section_pattern='## '):
    """
    Split markdown content into sections based on headers.
    
    Args:
        content (str): The markdown content to split
        section_pattern (str): The pattern to identify section headers (e.g. '## ' or '### ')
        
    Returns:
        list: A list of tuples containing (section_title, content) for each section
    """
    # Find all headers and their content
    sections = []
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        if line.startswith(section_pattern):
            # If we have a previous section, save it
            if current_section is not None:
                sections.append((current_section, '\n'.join(current_content).strip()))
            # Start new section
            current_section = line[len(section_pattern):].strip()  # Remove section prefix
            current_content = []
        else:
            # Strip trailing whitespace from each line
            current_content.append(line.rstrip())
    
    # Add the last section
    if current_section is not None:
        sections.append((current_section, '\n'.join(current_content).strip()))
    
    return sections

def process_tasks(content):
    """
    Process a section's content to extract completed items and mark uncompleted ones.
    Handles subtasks by moving completed subtasks to the Completed section while
    preserving their relationship to the parent task.
    
    Args:
        content (str): The content of a section
        
    Returns:
        tuple: (new_content, completed_items) where new_content is the processed content
               and completed_items is a list of completed task lines
    """
    completed_items = []
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        # Skip empty lines
        if not line:
            new_lines.append(line)
            i += 1
            continue
            
        # Find task line
        task_match = re.match(r'^(\s*)- \[([ x])\](.*?)$', line)
        if not task_match:
            new_lines.append(line)
            i += 1
            continue
            
        indent, status, task_content = task_match.groups()
        main_task = task_content.strip()
        
        # Collect subtasks
        subtasks = []
        j = i + 1
        while j < len(lines) and lines[j].startswith(indent + '  '):
            subtasks.append(lines[j])  # Keep the original line with indentation
            j += 1
            
        # Process completed subtasks
        completed_subtasks = []
        remaining_subtasks = []
        for subtask in subtasks:
            if '- [x]' in subtask:
                completed_subtasks.append(subtask)
            else:
                remaining_subtasks.append(subtask)
        
        # Handle the main task based on its status and subtasks
        if status == 'x' or (subtasks and all('- [x]' in subtask for subtask in subtasks)):
            # If the task is completed or all subtasks are completed, move everything to completed
            completed_task = f"{indent}- [x] {main_task}"
            if subtasks:
                completed_task += '\n' + '\n'.join(subtask for subtask in subtasks)
            completed_items.append(completed_task)
        else:
            # For tasks with some completed subtasks or uncompleted tasks
            if completed_subtasks:
                # Move completed subtasks to completed items, preserving parent task's original state
                completed_task = f"{indent}- [{status}] {main_task}"
                completed_task += '\n' + '\n'.join(subtask for subtask in completed_subtasks)
                completed_items.append(completed_task)
            
            # Add the main task with appropriate markers
            if not indent and status == ' ':
                # Split task into markers and content
                parts = main_task.split(' ', 1)
                if len(parts) > 1 and parts[0].startswith('>'):
                    # Add one more marker
                    markers = parts[0] + '>'
                    task_text = parts[1]
                else:
                    # First marker
                    markers = '>'
                    task_text = main_task
                
                new_lines.append(f"{indent}- [ ] {markers} {task_text}")
            else:
                new_lines.append(f"{indent}- [{status}] {main_task}")
            
            # Add remaining subtasks
            for subtask in remaining_subtasks:
                new_lines.append(subtask)
        
        i = j if subtasks else i + 1

    # Join lines and clean up multiple newlines
    new_content = '\n'.join(new_lines)
    new_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_content)
    # Remove leading newlines after the section header
    new_content = re.sub(r'(## [^\n]+)\n+', r'\1\n', new_content)

    return new_content, completed_items

def process_markdown_file(input_path, output_path=None):
    """
    Process a markdown file to move completed tasks to the Completed section.
    
    Args:
        input_path (str): Path to input file or '-' for stdin
        output_path (str): Path to output file or '-' for stdout. If None, same as input_path.
        
    Returns:
        int: Number of completed items moved
    """
    # Read input
    if input_path == '-':
        content = sys.stdin.read()
    else:
        with open(input_path, 'r') as file:
            content = file.read()

    # Get yesterday's date formatted as "Month Day, Year"
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")

    # Split into sections
    sections = split_into_sections(content)
    
    # Process Today and Tonight sections and collect completed items
    completed_items = []
    new_sections = []
    
    for title, section_content in sections:
        if title in ['Today', 'Tonight']:
            new_content, completed = process_tasks(section_content)
            completed_items.extend(completed)
            new_sections.append((title, new_content))
        else:
            new_sections.append((title, section_content))

    # If there are completed items, handle the Completed section
    if completed_items:
        # Find or create Completed section
        completed_section = None
        for i, (title, content) in enumerate(new_sections):
            if title == 'Completed':
                completed_section = (i, content)
                break

        if completed_section:
            # Merge with existing completed section
            i, existing_content = completed_section
            
            # Find all yesterday sections and their content
            yesterday_sections = re.finditer(rf'### {yesterday}.*?(?=###|\Z)', existing_content, flags=re.DOTALL)
            yesterday_items = []
            
            # Collect all items from existing yesterday sections
            for section in yesterday_sections:
                items = re.findall(r'^(\s*- \[x\].*?)$', section.group(0), re.MULTILINE)
                yesterday_items.extend(items)
            
            # Remove all yesterday sections
            existing_content = re.sub(rf'### {yesterday}.*?(?=###|\Z)', '', existing_content, flags=re.DOTALL)
            
            # Create new yesterday section with all items
            new_completed_content = f"### {yesterday}\n"
            for item in yesterday_items + completed_items:
                new_completed_content += f"{item}\n"
            
            # Add to existing content if any
            if existing_content.strip():
                new_completed_content = f"{existing_content.strip()}\n{new_completed_content}"
            
            new_sections[i] = ('Completed', new_completed_content)
        else:
            # Create new completed section
            new_completed_content = f"### {yesterday}\n"
            for item in completed_items:
                new_completed_content += f"{item}\n"
            new_sections.append(('Completed', new_completed_content))

    # Reconstruct the file content
    new_content = '\n'.join(f"## {title}\n{content}" for title, content in new_sections)

    # Write output
    if output_path == '-':
        sys.stdout.write(new_content)
    else:
        with open(output_path, 'w') as file:
            file.write(new_content)

    return len(completed_items)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process markdown tasks and move completed items to Completed section.')
    parser.add_argument('input', help='Input file path (use - for stdin)')
    parser.add_argument('output', nargs='?', help='Output file path (use - for stdout, defaults to input file)')
    args = parser.parse_args()
    
    output_path = args.output if args.output is not None else args.input
    completed_count = process_markdown_file(args.input, output_path)
    print(f"Moved {completed_count} completed items to the 'Completed' section.", file=sys.stderr)

import re
from datetime import datetime, timedelta
import sys

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
    
    Args:
        content (str): The content of a section
        
    Returns:
        tuple: (new_content, completed_items) where new_content is the processed content
               and completed_items is a list of completed task lines
    """
    completed_items = []
    new_content = content

    # Find completed items
    completed_pattern = r'^(\s*- \[x\].*?)$'
    completed_items = re.findall(completed_pattern, content, re.MULTILINE)

    # Find and process uncompleted items
    uncompleted_pattern = r'^(\s*- \[ \][ \t]+)(.*?)$'
    uncompleted_items = re.findall(uncompleted_pattern, content, re.MULTILINE)
    
    # Process each uncompleted item
    for checkbox, rest in uncompleted_items:
        # Check if there's already a '>' marker
        if rest.startswith('>'):
            # Add another '>' to existing markers
            new_item = f"{checkbox}>{rest}"
        else:
            # Add first '>' marker with a space
            new_item = f"{checkbox}> {rest}"
        
        # Replace the old item with the new one
        old_item = f"{checkbox}{rest}"
        new_content = new_content.replace(old_item, new_item)

    # Remove completed items from section and their trailing newlines
    for item in completed_items:
        # Remove the item and its trailing newline
        new_content = re.sub(rf'{re.escape(item)}\n?', '', new_content)

    # Clean up multiple newlines and ensure proper section formatting
    new_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_content)
    # Remove leading newlines after the section header
    new_content = re.sub(r'(## [^\n]+)\n+', r'\1\n', new_content)

    return new_content, completed_items

def process_markdown_file(file_path):
    # Read the file
    with open(file_path, 'r') as file:
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

    # Write the updated content back to the file
    with open(file_path, 'w') as file:
        file.write(new_content)

    return len(completed_items)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <markdown_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    completed_count = process_markdown_file(file_path)
    print(f"Moved {completed_count} completed items to the 'Completed' section.")

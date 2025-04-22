import re
from datetime import datetime, timedelta
import sys

def process_section(content, section_pattern):
    """Process a section to extract and remove completed items and mark uncompleted ones."""
    section = re.search(section_pattern, content, re.DOTALL)
    completed_items = []
    
    if section:
        section_content = section.group(0)
        new_section_content = section_content

        # Find completed items
        completed_pattern = r'^(\s*- \[x\].*?)$'
        completed_in_section = re.findall(completed_pattern, section_content, re.MULTILINE)
        completed_items.extend(completed_in_section)

        # Find and process uncompleted items
        uncompleted_pattern = r'^(\s*- \[ \][ \t]+)(.*?)$'
        uncompleted_items = re.findall(uncompleted_pattern, section_content, re.MULTILINE)
        
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
            new_section_content = new_section_content.replace(old_item, new_item)

        # Remove completed items from section and their trailing newlines
        for item in completed_in_section:
            # Remove the item and its trailing newline
            new_section_content = re.sub(rf'{re.escape(item)}\n?', '', new_section_content)

        # Clean up multiple newlines and ensure proper section formatting
        new_section_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_section_content)
        # Remove leading newlines after the section header
        new_section_content = re.sub(r'(## [^\n]+)\n+', r'\1\n', new_section_content)

        # Replace the section in the original content
        content = content.replace(section_content, new_section_content)
    
    return content, completed_items

def process_markdown_file(file_path):
    # Read the file
    with open(file_path, 'r') as file:
        content = file.read()

    # Get yesterday's date formatted as "Month Day, Year"
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")

    # Process Today and Tonight sections
    today_pattern = r'## Today\s*(?:\n.*?)*?(?=##|\Z)'
    tonight_pattern = r'## Tonight\s*(?:\n.*?)*?(?=##|\Z)'

    content, today_completed = process_section(content, today_pattern)
    content, tonight_completed = process_section(content, tonight_pattern)
    
    completed_items = today_completed + tonight_completed

    # Only proceed with creating/updating Completed section if there are completed items
    if completed_items:
        # Find or create Completed section
        completed_section = re.search(r'## Completed\s*(?:\n.*?)*?(?=##|\Z)', content, re.DOTALL)

        if completed_section:
            # Get all yesterday sections
            yesterday_sections = re.findall(rf'### {yesterday}\s*(?:\n.*?)*?(?=###|\Z)', completed_section.group(0), re.DOTALL)
            
            if yesterday_sections:
                # Merge all yesterday sections into one
                merged_yesterday_content = f"### {yesterday}\n"
                for section in yesterday_sections:
                    # Extract the items from each section (excluding the header)
                    items = re.findall(r'^(\s*- \[x\].*?)$', section, re.MULTILINE)
                    for item in items:
                        merged_yesterday_content += f"{item}\n"
                
                # Add new completed items
                for item in completed_items:
                    merged_yesterday_content += f"{item}\n"
                
                # Replace all yesterday sections with the merged one
                content = re.sub(rf'### {yesterday}\s*(?:\n.*?)*?(?=###|\Z)', merged_yesterday_content, completed_section.group(0), flags=re.DOTALL)
                content = content.replace(completed_section.group(0), content)
            else:
                # Create new yesterday section
                new_section = f"### {yesterday}\n"
                for item in completed_items:
                    new_section += f"{item}\n"

                # Add to completed section
                completed_content = completed_section.group(0)
                new_completed_content = completed_content.replace("## Completed", f"## Completed\n{new_section}")
                content = content.replace(completed_content, new_completed_content)
        else:
            # Create new Completed section with yesterday subsection
            new_section = f"## Completed\n### {yesterday}\n"
            for item in completed_items:
                new_section += f"{item}\n"

            # Add at the end of the file
            content += f"\n\n{new_section}"

    # Write the updated content back to the file
    with open(file_path, 'w') as file:
        file.write(content)

    return len(completed_items)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <markdown_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    completed_count = process_markdown_file(file_path)

    print(f"Moved {completed_count} completed items to the 'Completed' section.")

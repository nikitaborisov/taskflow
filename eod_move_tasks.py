import re
from datetime import datetime, timedelta
import sys

def process_markdown_file(file_path):
    # Read the file
    with open(file_path, 'r') as file:
        content = file.read()

    # Get yesterday's date formatted as "Month Day, Year"
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%B %d, %Y")

    # Find today and tonight sections
    today_pattern = r'## Today\s*(?:\n.*?)*?(?=##|\Z)'
    tonight_pattern = r'## Tonight\s*(?:\n.*?)*?(?=##|\Z)'

    today_section = re.search(today_pattern, content, re.DOTALL)
    tonight_section = re.search(tonight_pattern, content, re.DOTALL)

    completed_items = []

    # Process Today section
    if today_section:
        today_content = today_section.group(0)
        new_today_content = today_content

        # Find completed items
        completed_pattern = r'^(\s*- \[x\].*?)$'
        completed_in_today = re.findall(completed_pattern, today_content, re.MULTILINE)
        completed_items.extend(completed_in_today)

        # Remove completed items from Today section
        for item in completed_in_today:
            new_today_content = new_today_content.replace(item, '')

        # Clean up empty lines
        new_today_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_today_content)

        # Replace the section in the original content
        content = content.replace(today_content, new_today_content)

    # Process Tonight section
    if tonight_section:
        tonight_content = tonight_section.group(0)
        new_tonight_content = tonight_content

        # Find completed items
        completed_pattern = r'^(\s*- \[x\].*?)$'
        completed_in_tonight = re.findall(completed_pattern, tonight_content, re.MULTILINE)
        completed_items.extend(completed_in_tonight)

        # Remove completed items from Tonight section
        for item in completed_in_tonight:
            new_tonight_content = new_tonight_content.replace(item, '')

        # Clean up empty lines
        new_tonight_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_tonight_content)

        # Replace the section in the original content
        content = content.replace(tonight_content, new_tonight_content)

    # Find or create Completed section
    completed_section = re.search(r'## Completed\s*(?:\n.*?)*?(?=##|\Z)', content, re.DOTALL)

    if completed_section:
        # Check if yesterday's section already exists
        yesterday_section = re.search(rf'### {yesterday}\s*(?:\n.*?)*?(?=###|\Z)', completed_section.group(0), re.DOTALL)

        if yesterday_section:
            # Add to existing yesterday section
            new_yesterday_content = yesterday_section.group(0)
            for item in completed_items:
                new_yesterday_content += f"\n{item}"

            content = content.replace(yesterday_section.group(0), new_yesterday_content)
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

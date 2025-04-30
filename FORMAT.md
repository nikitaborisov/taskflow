# TODO File Format

This document describes the format for TODO files.

## Sections

Sections are defined using markdown headers (h1-h6). The level of the header determines the section hierarchy.

```markdown
# Top Level Section
## Subsection
### Sub-subsection
```

## Tasks

Tasks are defined using markdown task list items with optional procrastination indicators.

```markdown
- [ ] Regular task
- [x] Completed task
- [ ] > Procrastinated task
- [ ] >> Very procrastinated task
```

### Task Properties

1. **Completion Status**:
   - `[ ]` for incomplete tasks
   - `[x]` for completed tasks

2. **Procrastination Level**:
   - Number of '>' characters indicates procrastination level
   - No '>' means level 0
   - Each '>' increases the level by 1

3. **Subtasks**:
   - A task may include subtasks, indicated by an indented sublist
   - Nested subtasks are supported
   - Each level of indentation is 2 spaces

### Task Content

- Task content follows the checkbox and procrastination indicators

## Examples

### Basic Example
```markdown
# Today
- [ ] Buy groceries
- [x] Call mom  
- [ ] > Clean the house
  - [ ] Vacuum
  - [ ] Dust
```

### Complex Example
```markdown
# Work
## Morning
- [ ] Check emails
- [ ] > Review PRs
  - [ ] PR #123
  - [ ] PR #456

## Afternoon
- [ ] Team meeting
- [ ] >> Write documentation
  - [ ] API docs
  - [ ] User guide
    - [ ] Installation
    - [ ] Usage
```

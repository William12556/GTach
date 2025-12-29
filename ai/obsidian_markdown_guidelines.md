# Obsidian Markdown Guidelines

## Internal Link Formatting

### Universal Rule

Always use angle brackets for internal links, preserving spaces in header names:

```markdown
[Link Text](<#header name>)
```

### Examples

**Headers:**

```markdown
# Installation
## Test 1
### Environment Validation
```

**Links:**

```markdown
[Installation](<#installation>)
[Test 1](<#test 1>)
[Environment Validation](<#environment validation>)
```

### Anchor Format

- Convert header text to lowercase
- Preserve spaces (do not replace with hyphens)
- Remove special characters

### Common Errors

**Without Angle Brackets:**

```markdown
[Test 1](#test-1)        // May fail
```

**With Angle Brackets:**

```markdown
[Test 1](<#test 1>)      // Always works
```

### Best Practice

Use angle bracket syntax consistently to avoid navigation errors.

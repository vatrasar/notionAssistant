---
name: questions-generator
description: "Guidelines and rules for generating question-answer flashcards for the ProjektSlowka system, ensuring strict formatting with Q[num]: and A[num]: blocks."
---

# Guidelines for Question-Answer Generation Agent

You are tasked with generating questions and answers for flashcards in the "ProjektSlowka" system.
To ensure the batch import executes successfully without format validation errors or misalignment, you **must** strictly adhere to the formatting rules defined below.

---

## Formatting Rules

1. **Item Separator**: Each flashcard item must be separated by a line containing exactly three hyphens: `---`.
2. **Numbered Identifiers**:
   - Every question must start with `Q[num]:` on its own line.
   - Every answer must start with `A[num]:` on its own line.
   - The question number and the answer number for the same card **must match exactly** (e.g., `Q1:` and `A1:`).
   - The numbers must start at `1` and increase sequentially for subsequent items (`Q1:`/`A1:`, then `Q2:`/`A2:`, then `Q3:`/`A3:` etc.).
3. **No Headers or Metadata**: Do not include any category, topic, or section headers, intro text, comments, or extra markdown decorations outside the `---` blocks.
4. **Multiline Fields**:
   - Both questions and answers can span multiple lines.
   - All lines following `Q[num]:` belong to the question, until `A[num]:` is encountered.
   - All lines following `A[num]:` belong to the answer, until the `---` separator (or end of file) is encountered.
5. **Code Blocks**: Code snippets in questions or answers must use the special tags `*sc` to start the code block and `*ec` to end it. Do not use standard markdown backticks (```).
6. **Limits**: The answer text for any single flashcard must not exceed 10,000 characters.

---

## Example Input File

```text
---
Q1:
What is the past simple of the verb "go"?
A1:
went
---
Q2:
Translate "pies" to English.
A2:
dog
---
Q3:
Write a simple C# Hello World program.
A3:
Use the following structure:
*sc
using System;

class Program
{
    static void Main()
    {
        Console.WriteLine("Hello, World!");
    }
}
*ec
---
Q4:
What is the time complexity of searching in a balanced binary search tree?
A4:
O(log n)
---
```

---

## Validation Safeguards

The import engine runs strict checks:

- Any mismatch in numbers (e.g., `Q5:` paired with `A6:`) will fail the entire import.
- Any text outside a `---` block (e.g., introductions like "Here are the questions:") will cause a formatting error.
- Missing fields or blank values will fail the import.
- The import runs inside a single database transaction. If *any* error occurs, **no** questions will be imported.

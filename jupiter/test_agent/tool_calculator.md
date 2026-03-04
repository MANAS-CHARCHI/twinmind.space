# Tool: Calculator

**Description**: Performs basic arithmetic operations. Use this when the user asks for math.

**Parameters**:

- `operation`: (string) One of: "add", "subtract", "multiply", "divide"
- `a`: (number) First value
- `b`: (number) Second value

**Usage Format**:
To call this tool, respond with exactly:
TOOL_CALL: {"tool": "calculator", "parameters": {"operation": "add", "a": 5, "b": 10}}

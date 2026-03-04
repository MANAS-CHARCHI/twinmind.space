# Tool: Clock

**Description**: Accesses the current system time and date. Use this whenever the user asks "What time is it?", "What is today's date?", or "How late is it?".

**Parameters**:

- `format`: (string) Optional. Use "time" for just the clock, "date" for just the calendar, or "full" for both.

**Usage Format**:
To call this tool, respond with exactly:
TOOL_CALL: {"tool": "clock", "parameters": {"format": "full"}}

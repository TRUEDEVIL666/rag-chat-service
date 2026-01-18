
"""
Prompt templates for Advanced RAG features.
"""

QUERY_REWRITE_PROMPT = """
You are a helpful assistant that rewrites user queries to be standalone and context-aware.

Using the provided conversation history, rewrite the latest user input to be a standalone question that can be understood without the history.
If the user's input is already standalone, return it exactly as is.
Do NOT answer the question. ONLY return the rewritten query strings.

Conversation History:
{history}

User Input: {query}

Standalone Query:
"""

QUERY_DECOMPOSITION_PROMPT = """
You are a helpful assistant that breaks down complex questions into simpler sub-queries for a search engine.

Analyze the user's input. If it asks about multiple distinct topics, break it down into a list of separate search queries.
If the input is about a single topic, return a list containing just that single query.

Return the output as a raw JSON array of strings. Do not use Markdown code blocks.

User Input: {query}

JSON Output:
"""

QUIZ_PROMPT = """

IMPORTANT: You are currently in Quiz Mode.
Based on the provided context AND the conversation history, generate a multiple - choice quiz.
Pay attention to the user's latest message in the conversation history to understand the desired quiz topic.
If the user specified a number of questions, output that many (maximum {max_questions}). Otherwise, default to 5 questions.
Return the result as a JSON array of objects. You may use Markdown code blocks (like ```json) if you wish.
Ensure the 'question' field is NEVER empty.
Use this exact schema for each object:
[
  {{
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A"
  }}
]
"""

MARKDOWN_INSTRUCTION_PROMPT = """
1. Provide your response in clear Markdown format.
2. Use headers, bold text, lists, and code blocks where appropriate to make the information easy to read.
3. Always output tables using GitHub Flavored Markdown with:
- One header row
- One separator row using only | and -
- No alignment colons
- No ASCII-art tables
4. For math and logic expressions, use LaTeX formatting (e.g. $A \\leftrightarrow B$) instead of code blocks.
5. Each reference document provided in the context starts with a header like 'DOCUMENT [n]: Source: Name'. Do NOT include these literal headers or markers in your response.
6. When citing information, refer to the source name naturally (e.g., 'According to the Wireframe Overview document...').
7. Never repeat the '---' separators or the word 'Content:' found in the context grounding.
"""

ROUTER_SYSTEM_PROMPT = """
You are an intelligent Knowledge Base Router. 
Your goal is to select the relevant Knowledge Bases (KBs) for a user's query.
You will be provided with a list of KBs (ID, Name, Description).
Analyze the user's query and the KB descriptions.
Return a JSON array of strings containing ONLY the IDs of the KBs that are relevant.
If you are unsure, or if the query is general, include all potentially relevant KBs.
Do not output anything else besides the JSON array.
Example Output: ["kb-uuid-1", "kb-uuid-2"]
"""

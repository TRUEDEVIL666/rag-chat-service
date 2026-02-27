"""
GraphRAG Extraction Demo
------------------------
Demonstrates how to use LangExtract to build a Knowledge Graph from text.
"""

from langextract.providers.ollama import OllamaLanguageModel
import langextract as lx
from langextract.core.data import Extraction
import sys
import logging

# ==============================================================================
# CONFIG
# ==============================================================================

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

MODEL_ID = "PetrosStav/gemma3-tools:4b"  # Or your preferred model
OLLAMA_BASE_URL = "http://localhost:11434"

# ==============================================================================
# SCHEMA PROMPT (The "Ontology")
# ==============================================================================

SCHEMA_PROMPT = """
You are a Knowledge Graph builder.

EXTRACT TWO TYPES OF ENTITIES:
1. Concept: A key idea, object, or term (e.g., "Photosynthesis", "Glucose").
2. Relationship: A specific connection between two Concepts.
   - Format: "Source Concept -> RELATION -> Target Concept"
   - Example: "Plants -> REQUIRE -> Water"

RULES:
- Copy 'Concept' text verbatim from the input.
- For 'Relationship', use the format "Source -> RELATION -> Target".
- Keep relations simple (e.g., CAUSES, REQUIRES, IS_A).
"""

# ==============================================================================
# EXAMPLES (Few-Shot Learning)
# ==============================================================================

EXAMPLES = [
    lx.data.ExampleData(
        text="Plants use sunlight to perform photosynthesis.",
        extractions=[
            Extraction("Concept", "Plants"),
            Extraction("Concept", "sunlight"),
            Extraction("Concept", "photosynthesis"),
            Extraction("Relationship", "Plants -> USE -> sunlight"),
            Extraction("Relationship", "Plants -> PERFORM -> photosynthesis"),
            Extraction("Relationship",
                       "photosynthesis -> REQUIRES -> sunlight"),
        ],
    ),
    lx.data.ExampleData(
        text="Mitochondria are the powerhouse of the cell.",
        extractions=[
            Extraction("Concept", "Mitochondria"),
            Extraction("Concept", "cell"),
            Extraction("Relationship", "Mitochondria -> IS_PART_OF -> cell"),
            Extraction("Relationship",
                       "Mitochondria -> IS -> powerhouse of the cell"),
        ],
    ),
]

# ==============================================================================
# GRAPH BUILDER
# ==============================================================================


def build_knowledge_graph():
  print("--- GraphRAG Extraction Demo ---")

  text = """
    Cellular respiration is a metabolic pathway that breaks down glucose and produces ATP.
    The stages of cellular respiration include glycolysis, the citric acid cycle, and oxidative phosphorylation.
    Glycolysis occurs in the cytoplasm and does not require oxygen.
    """

  print(f"Input Text:\n{text.strip()}\n")
  print("Extracting Knowledge Graph...")

  try:
    model = OllamaLanguageModel(
        model_id=MODEL_ID,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
    )

    result = lx.extract(
        text_or_documents=text,
        model=model,
        prompt_description=SCHEMA_PROMPT,
        examples=EXAMPLES,
    )

    # Parse Results into a Graph Structure (Adjacency List)
    concepts = set()
    edges = []

    for ext in result.extractions:
      if ext.extraction_class == "Concept":
        concepts.add(ext.extraction_text)
      elif ext.extraction_class == "Relationship":
        # Parse "Source -> REL -> Target"
        parts = ext.extraction_text.split(" -> ")
        if len(parts) == 3:
          src, rel, tgt = parts
          edges.append((src, rel, tgt))
          concepts.add(src)
          concepts.add(tgt)

    print("\n--- Extracted Nodes (Concepts) ---")
    for c in sorted(concepts):
      print(f"  • {c}")

    print("\n--- Extracted Edges (Relationships) ---")
    for src, rel, tgt in edges:
      print(f"  ({src}) --[{rel}]--> ({tgt})")

    # Simulate a Graph Query
    query_node = "Glycolysis"
    print(f"\n--- Simulating Graph Query: '{query_node}' ---")

    found = False
    # Find outgoing edges
    for src, rel, tgt in edges:
      if src.lower() == query_node.lower():
        print(f"  • {query_node} {rel} {tgt}")
        found = True

    # Find incoming edges
    for src, rel, tgt in edges:
      if tgt.lower() == query_node.lower():
        print(f"  • {src} {rel} {query_node}")
        found = True

    if not found:
      print(f"  No relationships found for '{query_node}'.")

  except Exception as e:
    print(f"Extraction failed: {e}")
    import traceback
    traceback.print_exc()


if __name__ == "__main__":
  build_knowledge_graph()

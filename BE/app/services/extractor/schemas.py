try:
  from langextract.core.data import ExampleData, Extraction
except ImportError:
  # Try alternate location if direct import fails
  import langextract.data as lx_data
  ExampleData = lx_data.ExampleData
  Extraction = lx_data.Extraction

SCHEMA_PROMPT = """
You are performing span-based information extraction.

Rules:
- Copy verbatim spans.
- No paraphrasing.
- No JSON objects.
- Every source and target node in a Relationship MUST be extracted as an individual entity first.

Extract:

Concept
Person
Event
Date
Location
Formula
Quote
Relationship
"""

EXAMPLES = [
    ExampleData(
        text="Chiến dịch Điện Biên Phủ kết thúc thắng lợi vào năm 1954, do Đại tướng Võ Nguyên Giáp chỉ huy.",
        extractions=[
            Extraction("Event", "Chiến dịch Điện Biên Phủ"),
            Extraction("Date", "năm 1954"),
            Extraction("Person", "Đại tướng Võ Nguyên Giáp"),
            Extraction("Relationship", "Đại tướng Võ Nguyên Giáp || chỉ huy || Chiến dịch Điện Biên Phủ"),
            Extraction("Relationship", "Chiến dịch Điện Biên Phủ || kết thúc thắng lợi vào || năm 1954"),
        ],
    ),
    ExampleData(
        text="Quang hợp là quá trình thực vật sử dụng năng lượng ánh sáng chuyển hóa thành năng lượng hóa học.",
        extractions=[
            Extraction("Concept", "Quang hợp"),
            Extraction(
              "Concept", "quá trình thực vật sử dụng năng lượng ánh sáng chuyển hóa thành năng lượng hóa học"),
            Extraction("Relationship", "thực vật || sử dụng năng lượng ánh sáng || chuyển hóa thành năng lượng hóa học"),
        ],
    ),
    ExampleData(
        text="Theo định luật II Newton, gia tốc của một vật cùng hướng với lực tác dụng lên vật, công thức F=ma.",
        extractions=[
            Extraction("Person", "Newton"),
            Extraction("Concept", "định luật II Newton"),
            Extraction("Formula", "F=ma"),
            Extraction("Relationship", "định luật || có công thức || F=ma"),
        ],
    )
]

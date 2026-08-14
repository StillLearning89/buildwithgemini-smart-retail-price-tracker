from frontend.main import _try_parse_a2ui_text, _extract_parts
from a2a.types import TextPart, Part

def test_a2ui_text_extraction():
    # Test wrapped <a2a_datapart_json>
    raw_wrapped = '<a2a_datapart_json>{"kind": "data", "metadata": {"mimeType": "application/json+a2ui"}, "data": {"beginRendering": {"root": "r1"}}}</a2a_datapart_json>'
    parsed = _try_parse_a2ui_text(raw_wrapped)
    assert len(parsed) == 1
    assert "beginRendering" in parsed[0]

def test_extract_parts_with_a2ui():
    raw_wrapped = '<a2a_datapart_json>{"kind": "data", "metadata": {"mimeType": "application/json+a2ui"}, "data": {"beginRendering": {"root": "r1"}}}</a2a_datapart_json>'
    part = Part(root=TextPart(text=raw_wrapped))
    extracted = _extract_parts([part])
    assert len(extracted) == 1
    assert extracted[0]["kind"] == "a2ui"
    assert "beginRendering" in extracted[0]["data"]

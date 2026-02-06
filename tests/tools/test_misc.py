from asas_mcp.tools import misc

def test_identify_file_type():
    # PNG magic bytes
    png_header = b'\x89PNG\r\n\x1a\n'
    result = misc.identify_file_type(png_header)
    assert result["type"] == "PNG"
    assert result["mime"] == "image/png"

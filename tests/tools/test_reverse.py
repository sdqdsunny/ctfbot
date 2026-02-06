from asas_mcp.tools import reverse

def test_extract_strings():
    # 模拟二进制数据
    binary_data = b'Hello\x00\x00World\x00Test\x00'
    result = reverse.extract_strings(binary_data, min_length=4)
    assert "Hello" in result
    assert "World" in result
    assert "Test" in result

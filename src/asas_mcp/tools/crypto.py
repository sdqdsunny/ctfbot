import base64
from urllib.parse import unquote

def caesar_cipher(text: str, shift: int) -> str:
    result = ""
    for char in text:
        if char.isalpha():
            start = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - start + shift) % 26 + start)
        else:
            result += char
    return result

def morse_decode(content: str) -> str:
    MORSE_CODE_DICT = {
        '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
        '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
        '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
        '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
        '-.--': 'Y', '--..': 'Z', '.----': '1', '..---': '2', '...--': '3',
        '....-': '4', '.....': '5', '-....': '6', '--...': '7', '---..': '8',
        '----.': '9', '-----': '0', '--..--': ', ', '.-.-.-': '.', '..--..': '?',
        '-..-.': '/', '-....-': '-', '-...--': '(', '-.--.-': ')'
    }
    content = content.strip().replace(' / ', ' ').replace('/', ' ')
    words = content.split('   ')
    decoded_words = []
    for word in words:
        chars = word.split(' ')
        decoded_chars = [MORSE_CODE_DICT.get(c, '?') for c in chars if c]
        decoded_words.append("".join(decoded_chars))
    return " ".join(decoded_words)

def decode(content: str, method: str = "auto") -> str:
    if method == "base64":
        return base64.b64decode(content).decode('utf-8', errors='ignore')
    elif method == "hex":
        return bytes.fromhex(content).decode('utf-8', errors='ignore')
    elif method == "url":
        return unquote(content)
    elif method == "rot13":
        return caesar_cipher(content, 13)
    elif method == "caesar":
        # If method is caesar but no shift provided, try all 25 shifts
        results = []
        for s in range(1, 26):
            results.append(f"Shift {s}: {caesar_cipher(content, s)}")
        return "\n".join(results)
    elif method == "morse":
        return morse_decode(content)
        
    # Simple auto-detection for Base64
    if method == "auto":
        try:
            if len(content) % 4 == 0 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in content):
                return f"[Auto-Base64] {base64.b64decode(content).decode('utf-8', errors='ignore')}"
        except:
            pass
            
    return content

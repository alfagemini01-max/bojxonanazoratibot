from __future__ import annotations

import re
import sys
import zlib
from pathlib import Path


def unescape_pdf_string(value: bytes) -> str:
    out = bytearray()
    index = 0
    while index < len(value):
        char = value[index]
        if char != 92:
            out.append(char)
            index += 1
            continue
        index += 1
        if index >= len(value):
            break
        esc = value[index]
        index += 1
        if esc in b"nrtbf":
            out.append({ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12}[esc])
        elif esc in b"()\\":
            out.append(esc)
        elif 48 <= esc <= 55:
            octal = bytes([esc])
            for _ in range(2):
                if index < len(value) and 48 <= value[index] <= 55:
                    octal += bytes([value[index]])
                    index += 1
            out.append(int(octal, 8))
        else:
            out.append(esc)
    raw = bytes(out)
    for encoding in ("utf-16-be", "utf-8", "cp1251", "latin1"):
        try:
            text = raw.decode(encoding)
            if sum(ch.isprintable() or ch.isspace() for ch in text) / max(len(text), 1) > 0.75:
                return text
        except UnicodeDecodeError:
            pass
    return raw.decode("latin1", errors="ignore")


def main() -> None:
    data = Path(sys.argv[1]).read_bytes()
    chunks: list[bytes] = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        stream = match.group(1)
        prefix = data[max(0, match.start() - 250) : match.start()]
        if b"FlateDecode" in prefix:
            try:
                stream = zlib.decompress(stream)
            except zlib.error:
                pass
        chunks.append(stream)
    text_parts: list[str] = []
    for chunk in chunks:
        for item in re.findall(rb"\((?:\\.|[^\\()])*\)\s*Tj", chunk):
            text_parts.append(unescape_pdf_string(item[1 : item.rfind(b")")]))
        for array in re.findall(rb"\[(.*?)\]\s*TJ", chunk, re.S):
            for value in re.findall(rb"\((?:\\.|[^\\()])*\)", array):
                text_parts.append(unescape_pdf_string(value[1:-1]))
            text_parts.append("\n")
    text = "".join(text_parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    print(text)


if __name__ == "__main__":
    main()

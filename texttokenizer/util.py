from pathlib import Path

from .token import Token


def suffix_path(src: Path, suffix: str, ext=".pdf") -> Path:
    """Returns a new path with a suffix appended, from the original given path."""
    dest_name = src.with_suffix("").name + f"-{suffix}{ext}"
    return src.with_name(dest_name)


def expand_page_list(pages: str, maxIdx: int, minIdx=0) -> list[int]:
    """Returns a list of page indices from the given page range."""
    expanded = set()
    if not pages:
        return list(range(minIdx, maxIdx + 1))
    for item in pages.split(","):
        item = item.strip()
        if "-" in item:
            start, end = map(int, item.split("-"))
            group = range(max(minIdx, start), min(maxIdx, end) + 1)
            expanded.update(group)
        else:
            expanded.add(int(item))
    return list(expanded)


def merge_bboxes(tokens: list[Token]) -> list[Token]:
    """Merge tokens using heuristics on token bounding boxes."""
    sorted_tokens = sorted(
        tokens, key=lambda token: (token.page, token.bbox[1], token.bbox[0])
    )
    merged_tokens = []
    current_token = sorted_tokens[0]
    for token in sorted_tokens[1:]:
        cpage, page = current_token.page, token.page
        ctext, text = current_token.text, token.text
        corig, orig = current_token.origin, token.origin
        cfont, font = current_token.font, token.font
        cx1, cy1, cx2, cy2 = current_token.bbox
        x1, y1, x2, y2 = token.bbox
        if (
            (page == cpage)
            and (font == cfont)
            and (y1 == cy1)
            and (x1 == cx2 or x2 == cx1)
        ):
            args = {
                "page": page,
                "font": font,
                "bbox": (min(x1, cx1), y1, max(x2, cx2), max(y2, cy2)),
                "text": " ".join([ctext, text] if cx2 == x1 else [text, ctext]),
                "origin": corig if cx2 == x1 else orig,
            }
            current_token = Token(**args)
        else:
            merged_tokens.append(current_token)
            current_token = token
    if not merged_tokens or current_token.text != merged_tokens[-1].text:
        merged_tokens.append(current_token)
    return merged_tokens


FONT_FLAGS = {
    "superscript": 2**0,
    "italic": 2**1,
    "serif": 2**2,
    "mono": 2**3,
    "bold": 2**4,
}


def flag_composer(flags: dict) -> int:
    """Computes a font flags int from the given font flags."""
    result = 0
    for k, v in FONT_FLAGS.items():
        if flags.get(k):
            result |= v
    return result


def flags_decomposer(flags: int) -> dict:
    """Decomposes the given font flag int into flags."""
    result = {k: bool(flags & v) for k, v in FONT_FLAGS.items()}
    result["sans"] = not result["serif"]
    result["proportional"] = not result["mono"]
    return result

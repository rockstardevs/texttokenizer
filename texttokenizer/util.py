from pathlib import Path
from typing import List

from .token import Token


def suffix_path(src: Path, suffix: str, ext=".pdf") -> Path:
    """Returns a new path with a suffix appended, from the original given path."""
    dest_name = src.with_suffix("").name + f"-{suffix}{ext}"
    return src.with_name(dest_name)


def expand_page_list(pages: str, maxIdx: int, minIdx=0) -> List[int]:
    """Returns a list of page indices from the given page range."""
    expanded = set()
    for item in pages.split(","):
        item = item.strip()
        if "-" in item:
            start, end = map(int, item.split("-"))
            group = range(max(minIdx, start), min(maxIdx, end) + 1)
            expanded.update(group)
        else:
            expanded.add(int(item))
    return list(expanded)


def merge_bboxes(tokens: List[Token]) -> List[Token]:
    """Merge tokens using heuristics on token bounding boxes."""
    sorted_tokens = sorted(
        tokens, key=lambda token: (token.page, token.bbox[1], token.bbox[0])
    )
    merged_tokens = []
    current_token = sorted_tokens[0]
    for token in sorted_tokens[1:]:
        cpage, page = current_token.page, token.page
        ctext, text = current_token.text, token.text
        cfont, font = current_token.font, token.font
        cx1, cy1, cx2, cy2 = current_token.bbox
        x1, y1, x2, y2 = token.bbox
        if (
            (page == cpage)
            and (font == cfont)
            and (y1 == cy1)
            and (x1 == cx2 or x2 == cx1)
        ):
            new_bbox = (min(x1, cx1), y1, max(x2, cx2), max(y2, cy2))
            new_text = [ctext, text] if cx2 == x1 else [text, ctext]
            current_token = Token(
                page=page, font=font, bbox=new_bbox, text=" ".join(new_text)
            )
        else:
            merged_tokens.append(current_token)
            current_token = token
    if not merged_tokens or current_token.text != merged_tokens[-1].text:
        merged_tokens.append(current_token)
    return merged_tokens

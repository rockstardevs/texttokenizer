from dataclasses import dataclass
from typing import Tuple, TypeAlias

Font: TypeAlias = Tuple[str, float]


@dataclass(kw_only=True)
class Token:
    page: int
    text: str
    font: Font
    origin: Tuple[float, float]
    bbox: Tuple[float, float, float, float]

    def __repr__(self):
        return f"page:{self.page} text:{self.text} bbox:{self.bbox} font:{self.font}"

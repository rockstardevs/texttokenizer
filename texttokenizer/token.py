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

    @classmethod
    def csv_headers(self) -> Tuple[str]:
        return ("page", "text", "font", "origin", "bbox")

    def __repr__(self):
        return f"page:{self.page} text:{self.text} font:{self.font} bbox:{self.bbox} origin:{self.origin}"

    def as_csv_row(self) -> Tuple:
        return ({self.page}, {self.text}, {self.font}, {self.origin}, {self.bbox})

    def as_templatizer_dict(self):
        return {
            "page": self.page,
            "origin": self.origin,
            "text": self.text,
        }

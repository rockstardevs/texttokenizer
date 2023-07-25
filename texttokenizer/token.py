from dataclasses import dataclass
from typing import TypeAlias

Font: TypeAlias = tuple[str, float]
TokenKey: TypeAlias = tuple[int, tuple[float, float], str]


@dataclass(kw_only=True)
class Token:
    page: int
    text: str
    font: Font
    origin: tuple[float, float]
    bbox: tuple[float, float, float, float]

    @classmethod
    def csv_headers(self) -> tuple[str]:
        return ("page", "text", "font", "origin", "bbox")

    def __repr__(self):
        return f"page:{self.page} text:{self.text} font:{self.font} bbox:{self.bbox} origin:{self.origin}"

    def key(self) -> TokenKey:
        return (self.page, self.origin, self.text)

    def as_csv_row(self) -> tuple:
        return ({self.page}, {self.text}, {self.font}, {self.origin}, {self.bbox})

    def as_templatizer_dict(self):
        return {
            "page": self.page,
            "origin": self.origin,
            "text": self.text,
        }

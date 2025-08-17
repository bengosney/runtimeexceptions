import re


class MarkedString(str):
    marker: str

    def __new__(cls, value: str, marker: str):
        obj = super().__new__(cls, value)
        obj.marker = marker
        return obj

    def __str__(self):
        return f"{self.marker}{super().__str__()}{self.marker}"

    def remove_from_text(self, text: str) -> str:
        pattern = re.escape(self.marker) + r".*?" + re.escape(self.marker)
        return re.sub(pattern, "", text, 1)

    def replace_in_text(self, text: str) -> str:
        pattern = re.escape(self.marker) + r".*?" + re.escape(self.marker)
        return re.sub(pattern, str(self), text, 1)

    def replace_or_append(self, text: str, joiner: str = " ") -> str:
        if self.marker in text:
            return self.replace_in_text(text)
        return f"{text}{joiner}{self}"

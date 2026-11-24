import re

LINK = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+)\)")


class Issue:
    def __init__(self, text: str) -> None:
        self.text = text

    @classmethod
    def from_file(cls, path: str) -> "Issue":
        with open(path, encoding="utf-8") as file:
            return cls(file.read())

    def find_line(self, prefix: str) -> str | None:
        for line in self.text.splitlines():
            if line.startswith(prefix):
                return line[len(prefix):]
        return None

    @property
    def subject(self) -> str | None:
        line = self.find_line("Subject:")
        return None if line is None else line.strip()

    @property
    def preview(self) -> str | None:
        line = self.find_line("Preview:")
        return None if line is None else line.strip()

    @property
    def body(self) -> str:
        lines = self.text.splitlines()
        return "\n".join(line for line in lines if not line.startswith(("Subject:", "Preview:"))).strip()

    @property
    def links(self) -> list[str]:
        return LINK.findall(self.text)

    def personalize(self, first_name: str) -> str:
        return self.text.replace("{{first_name}}", first_name)

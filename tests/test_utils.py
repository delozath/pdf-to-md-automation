import pytest

from pdf_marker_transcriber.utils import markdown_sanitizer


class TestMarkdownSanitizer:
    @pytest.fixture
    def valid_markdown(self) -> str:
        return (
            "# Heading\n\n"
            "A **bold** statement with `inline_code`.\n\n"
            "- first item\n"
            "- second item\n"
        )

    @pytest.mark.parametrize(
        ("markdown", "expected"),
        [
            pytest.param("‘quoted’", "'quoted'", id="single-quotes"),
            pytest.param("“quoted”", '"quoted"', id="double-quotes"),
            pytest.param(
                "page 10–12 — notes",
                "page 10-12 - notes",
                id="dashes",
            ),
            pytest.param(
                "â€œquotedâ€\x9d â€“ notes",
                '"quoted" - notes',
                id="mojibake",
            ),
        ],
    )
    def test_normalizes_supported_punctuation(
        self,
        markdown: str,
        expected: str,
    ) -> None:
        assert markdown_sanitizer(markdown) == expected

    def test_preserves_valid_markdown(self, valid_markdown: str) -> None:
        assert markdown_sanitizer(valid_markdown) == valid_markdown

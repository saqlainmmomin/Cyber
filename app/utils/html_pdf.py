"""Offline HTML-to-PDF rendering for client deliverables."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname


REPO_ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = REPO_ROOT / "app" / "assets" / "fonts" / "noto"
FONT_FILES = {
    "NotoSans-Regular.ttf": "f3961a9cde016d41a4879aecda1474d3a36d6bf54fa0e4643de029cc2248b0e8",
    "NotoSans-Bold.ttf": "87cb2d84472a7d66da659ee47b6cdb9552326e8c128245231f191b6ac72529d9",
    "NotoSansDevanagari-Regular.ttf": "9c7d935139ea6a1e6ad9dbac4f6d27ece1e04bca8123c8888d00a0f9df4724cd",
    "NotoSansDevanagari-Bold.ttf": "ff2f76a23aad41e0608c2d7dbc4bacd247ff3bec78f0ec2a8fb106b561636e58",
}
DISPLAY_FONT_FILES = {
    "BarlowCondensed-Bold.ttf": "e476562ec9c1e16cf16475895b511f08c804f438cc9a9f80a44ea50a0eeb5b65",
    "BarlowCondensed-SemiBold.ttf": "7b619d14bc2327509a9ef32b0890f709626f7ecc9ff61191c2a4314c5499d2d9",
}
LICENSE_FILES = ("OFL-NotoSans.txt", "OFL-NotoSansDevanagari.txt")
DISPLAY_LICENSE_FILES = ("OFL-BarlowCondensed.txt",)
FONT_STACK = "'Noto Sans', 'Noto Sans Devanagari'"
REQUIRE_ENV = "CYBERASSESS_REQUIRE_WEASYPRINT"
RENDERER_UNAVAILABLE_MESSAGE = (
    "PDF rendering is unavailable on this server: WeasyPrint or its system "
    "libraries (Pango) are not installed."
)
OFFLINE_REFUSED_MESSAGE = "The report tried to load an external resource: {url}"


class RendererUnavailable(RuntimeError):
    def __init__(self, reason: str | None = None):
        self.message = RENDERER_UNAVAILABLE_MESSAGE
        self.reason = reason
        super().__init__(self.message)


class OfflineRenderError(RuntimeError):
    def __init__(self, url: str):
        self.url = url
        self.message = OFFLINE_REFUSED_MESSAGE.format(url=url)
        super().__init__(self.message)


def weasyprint_status() -> tuple[bool, str | None]:
    try:
        import weasyprint
    except (ImportError, OSError) as exc:
        return False, f"{type(exc).__name__}: {exc}"
    return True, None


def renderer_label() -> str:
    try:
        import weasyprint
    except (ImportError, OSError) as exc:
        raise RendererUnavailable(f"{type(exc).__name__}: {exc}") from exc
    return f"weasyprint {weasyprint.__version__}"


def font_face_css() -> str:
    return "\n".join(
        (
            "@font-face { font-family: 'Noto Sans'; src: url('NotoSans-Regular.ttf'); "
            "font-weight: 400; font-style: normal; }",
            "@font-face { font-family: 'Noto Sans'; src: url('NotoSans-Bold.ttf'); "
            "font-weight: 700; font-style: normal; }",
            "@font-face { font-family: 'Noto Sans Devanagari'; "
            "src: url('NotoSansDevanagari-Regular.ttf'); font-weight: 400; "
            "font-style: normal; }",
            "@font-face { font-family: 'Noto Sans Devanagari'; "
            "src: url('NotoSansDevanagari-Bold.ttf'); font-weight: 700; "
            "font-style: normal; }",
        )
    )


def display_font_face_css() -> str:
    return "\n".join(
        (
            "@font-face { font-family: 'Display'; src: url('BarlowCondensed-Bold.ttf'); "
            "font-weight: 700; font-style: normal; }",
            "@font-face { font-family: 'Display'; src: url('BarlowCondensed-SemiBold.ttf'); "
            "font-weight: 600; font-style: normal; }",
        )
    )


def render_pdf(html: str) -> bytes:
    available, reason = weasyprint_status()
    if not available:
        raise RendererUnavailable(reason)

    import weasyprint
    from weasyprint.urls import FatalURLFetchingError, URLFetcher

    font_dir = FONT_DIR.resolve()

    class _OfflineURLRefused(FatalURLFetchingError):
        def __init__(self, url: str):
            self.url = url
            super().__init__(url)

    class _OfflineFetcher(URLFetcher):
        def fetch(self, url, headers=None):
            parts = urlsplit(url)
            if parts.scheme.lower() == "file":
                path = Path(url2pathname(unquote(parts.path))).resolve()
                if path.parent == font_dir and path.name in (FONT_FILES | DISPLAY_FONT_FILES):
                    return super().fetch(url, headers)
            raise _OfflineURLRefused(url)

    try:
        return weasyprint.HTML(
            string=html,
            base_url=f"{font_dir}{os.sep}",
            url_fetcher=_OfflineFetcher(),
        ).write_pdf()
    except _OfflineURLRefused as exc:
        raise OfflineRenderError(exc.url) from None

# -*- coding: utf-8 -*-
"""Bundle Sri Shyam site into one HTML file (CSS + JS inlined). Images/fonts stay as relative paths."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "sri-shyam-kulfi.html"

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")

def fix_css(css: str, from_dir: str) -> str:
    """Rewrite url(...) so paths work from site root (where the HTML lives)."""
    base = Path(from_dir)

    def repl(m):
        raw = m.group(1).strip().strip("'\"")
        if raw.startswith(("data:", "http://", "https://", "//", "#")):
            return m.group(0)
        # strip query/hash for path resolve, keep suffix
        path_part, *rest = re.split(r"([?#].*)", raw, maxsplit=1)
        suffix = "".join(rest)
        resolved = (base / path_part).resolve()
        try:
            rel = resolved.relative_to(ROOT).as_posix()
        except ValueError:
            rel = path_part
        return f"url({rel}{suffix})"

    css = re.sub(r"url\(([^)]+)\)", repl, css)
    # drop @import lines (we'll inline those files ourselves)
    css = re.sub(r'@import\s+url\([^)]+\);\s*', '', css)
    return css

# Order matters
css_parts = [
    fix_css(read("css/base.css"), "css"),
    fix_css(read("css/vendor.css"), "css"),
    fix_css(read("css/font-awesome/css/font-awesome.min.css"), "css/font-awesome/css"),
    fix_css(read("css/micons/micons.css"), "css/micons"),
    fix_css(read("css/fonts.css"), "css"),
    fix_css(read("css/main.css"), "css"),
    fix_css(read("css/kulfi.css"), "css"),
]
bundled_css = "\n\n".join(css_parts)

js_parts = [
    read("js/modernizr.js"),
    read("js/pace.min.js"),
    read("js/jquery-2.1.3.min.js"),
    read("js/plugins.js"),
    read("js/main.js"),
]
bundled_js = "\n;\n".join(js_parts)

extra_js = r"""
(function ($) {
  if ($('#menu-gallery').length && $.fn.lightGallery) {
    $('#menu-gallery').lightGallery({ selector: 'a.menu-board', download: false });
  }
  if ($('#kulfi-gallery').length && $.fn.lightGallery) {
    $('#kulfi-gallery').lightGallery({ selector: 'a.kulfi-shot', download: false });
  }
  var $slides = $('#home .hero-slide');
  if ($slides.length > 1) {
    var i = 0;
    setInterval(function () {
      $slides.eq(i).removeClass('is-active');
      i = (i + 1) % $slides.length;
      $slides.eq(i).addClass('is-active');
    }, 4500);
  }
})(jQuery);
"""

# Body from current index.html (between <body> and scripts)
html = read("index.html")
# extract body inner without external script/link tags we'll replace
m = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL | re.IGNORECASE)
if not m:
    raise SystemExit("No body found in index.html")
body = m.group(1)
# strip existing script tags and leave markup
body = re.sub(r"<script\b[^>]*>.*?</script>", "", body, flags=re.DOTALL | re.IGNORECASE)
body = body.strip()

doc = f"""<!DOCTYPE html>
<html class="no-js" lang="en">
<head>
<meta charset="utf-8">
<title>Sri Shyam Kulfi &amp; Ice Cream | Taste the Tradition</title>
<meta name="description" content="Sri Shyam Kulfi &amp; Ice Cream in Coimbatore — handmade kulfi, falooda, milkshakes &amp; ice cream. Free home delivery. Order on WhatsApp, Swiggy or Zomato.">
<meta name="author" content="Sri Shyam Kulfi &amp; Ice Cream">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<link rel="shortcut icon" href="favicon.ico" type="image/x-icon">
<link rel="icon" href="favicon.ico" type="image/x-icon">
<style>
{bundled_css}
</style>
</head>
<body id="top">
{body}
<script>
{bundled_js}
;
{extra_js}
</script>
</body>
</html>
"""

OUT.write_text(doc, encoding="utf-8")
print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes)")

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_game_javascript_element_ids_exist_in_template():
    template = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    template_ids = set(re.findall(r'\bid="([^"]+)"', template))
    queried_ids = set()
    for filename in ("game.js", "ui.js"):
        script = (ROOT / "static" / "js" / filename).read_text(encoding="utf-8")
        queried_ids.update(re.findall(r'\$\("([^"]+)"\)', script))
    assert queried_ids <= template_ids


def test_frontend_dependencies_are_served_locally():
    template = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert "cdnjs.cloudflare.com" not in template
    assert "https://" not in template
    assert (ROOT / "static" / "vendor" / "socket.io.min.js").is_file()
    assert (ROOT / "static" / "favicon.svg").is_file()
    assert not list((ROOT / "static" / "images").glob("bonhomme*.gif"))
    for module in ("game.js", "ui.js", "characters.js", "bots.js", "audio.js"):
        assert (ROOT / "static" / "js" / module).is_file()

    for module_path in (ROOT / "static" / "js").glob("*.js"):
        imports = re.findall(r'from\s+["\']([^"\']+)["\']', module_path.read_text(encoding="utf-8"))
        assert all(
            (module_path.parent / import_path).is_file()
            for import_path in imports
            if import_path.startswith(".")
        )


def test_accessibility_and_reduced_motion_are_part_of_the_ui():
    template = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "static" / "css" / "style.css").read_text(encoding="utf-8")
    assert '<html lang="fr">' in template
    assert 'name="viewport"' in template
    assert "prefers-reduced-motion: reduce" in css
    assert 'aria-live="polite"' in template

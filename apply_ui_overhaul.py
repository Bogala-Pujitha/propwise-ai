
from pathlib import Path
import shutil
import re
from datetime import datetime

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / (".ui_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))


def backup(rel):
    src = ROOT / rel
    if not src.exists():
        return
    dst = BACKUP / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def ensure_css_links():
    views = ROOT / "app" / "views"
    css_line = "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/ui_overhaul.css') }}\">"

    for path in views.glob("*.html"):
        text = path.read_text(encoding="utf-8")

        if "ui_overhaul.css" not in text:
            match = re.search(
                r"<link[^>]+style\\.css[^>]*>",
                text,
                flags=re.I,
            )

            if match:
                text = (
                    text[:match.end()]
                    + "\n"
                    + css_line
                    + text[match.end():]
                )

        path.write_text(text, encoding="utf-8")


def patch_dashboard():
    path = ROOT / "app" / "views" / "dashboard.html"
    backup("app/views/dashboard.html")
    text = path.read_text(encoding="utf-8")

    text = re.sub(
        r"\\s*<link[^>]+leaflet[^>]+>\\s*",
        "\n",
        text,
        flags=re.I,
    )

    text = re.sub(
        r"\\s*<script[^>]+leaflet[^>]+></script>\\s*",
        "\n",
        text,
        flags=re.I,
    )

    color_block = re.compile(
        r"var\\s+propertyTypeColors\\s*=\\s*\\{.*?\\};",
        re.S,
    )

    new_colors = (
        "var propertyTypeColors = {\n"
        "        'Apartment': '#2F6F66',\n"
        "        'House': '#3F6D8F',\n"
        "        'Villa': '#B85C38',\n"
        "        'Plot': '#B68B2E'\n"
        "    };"
    )

    text = color_block.sub(
        new_colors,
        text,
        count=1,
    )

    text = text.replace(
        "var barColors = ['#4f46e5'];",
        "var barColors = ['#25313B'];",
    )

    text = text.replace(
        "backgroundColor: ['#4f46e5', '#4f46e5', '#4f46e5'],",
        "backgroundColor: ['#A6ADB2', '#2F6F66', '#3F6D8F'],",
    )

    text = text.replace(
        "borderColor: '#4f46e5',",
        "borderColor: '#2F6F66',",
    )

    text = text.replace(
        "backgroundColor: 'rgba(79, 70, 229, 0.1)',",
        "backgroundColor: 'rgba(47, 111, 102, 0.10)',",
    )

    text = text.replace(
        "pointBackgroundColor: '#4f46e5'",
        "pointBackgroundColor: '#2F6F66'",
    )

    text = text.replace(
        "Your Property",
        "Property Inventory",
        1,
    )

    render_start = text.find(
        "    function renderMap(r, inputData) {"
    )

    filters_start = text.find(
        "    function populateMapFilters(r, inputData) {"
    )

    if (
        render_start == -1
        or filters_start == -1
        or filters_start <= render_start
    ):
        raise RuntimeError(
            "Could not locate dashboard map function."
        )

    new_render_map = (
        "    function renderMap(r, inputData) {\n"
        "        if (window.PW_renderDashboardMap) {\n"
        "            window.PW_renderDashboardMap(r, inputData);\n"
        "        }\n"
        "    }\n\n"
    )

    text = (
        text[:render_start]
        + new_render_map
        + text[filters_start:]
    )

    if "propwise_maps.js" not in text:
        injection = (
            "<script>\n"
            "window.PROPWISE_GOOGLE_MAPS_KEY = "
            "{{ config.get('GOOGLE_MAPS_API_KEY', '')|tojson }};\n"
            "</script>\n"
            "<script src=\"{{ url_for('static', filename='js/propwise_maps.js') }}\"></script>\n"
        )

        text = text.replace(
            "</body>",
            injection + "</body>",
            1,
        )

    path.write_text(text, encoding="utf-8")


def patch_model_performance():
    path = ROOT / "app" / "views" / "model_performance.html"
    backup("app/views/model_performance.html")
    text = path.read_text(encoding="utf-8")

    text = re.sub(
        r"const colors\\s*=\\s*\\[[^;]+;",
        "const colors = ['#2F6F66','#3F6D8F','#B85C38','#B68B2E'];",
        text,
        count=1,
    )

    text = re.sub(
        r"const colorsLight\\s*=\\s*\\[[^;]+;",
        "const colorsLight = ['rgba(47,111,102,.12)','rgba(63,109,143,.12)','rgba(184,92,56,.12)','rgba(182,139,46,.12)'];",
        text,
        count=1,
    )

    path.write_text(text, encoding="utf-8")


def patch_market_intelligence():
    path = ROOT / "app" / "views" / "market_intelligence.html"
    backup("app/views/market_intelligence.html")
    text = path.read_text(encoding="utf-8")

    text = text.replace(
        "stats.type_distribution",
        "stats.property_types",
    )

    path.write_text(text, encoding="utf-8")


def patch_experiments_route():
    path = ROOT / "app" / "__init__.py"
    backup("app/__init__.py")
    text = path.read_text(encoding="utf-8")

    start = text.find("@app.route('/experiments')")
    if start == -1:
        start = text.find('@app.route("/experiments")')

    end = text.find("@app.route('/admin')", start)
    if end == -1:
        end = text.find('@app.route("/admin")', start)

    if start == -1 or end == -1:
        raise RuntimeError(
            "Could not locate /experiments route."
        )

    route = (
        "@app.route('/experiments')\n"
        "@login_required\n"
        "def experiments():\n"
        "    from app.services.experiment_discovery import discover_experiments\n\n"
        "    models_dir = os.path.join(BASE_DIR, '..', 'models')\n"
        "    experiments_data = discover_experiments(models_dir)\n\n"
        "    best_models = {}\n"
        "    best_path = os.path.join(models_dir, 'all_models_metadata.json')\n\n"
        "    if os.path.exists(best_path):\n"
        "        with open(best_path, encoding='utf-8') as handle:\n"
        "            best_models = json.load(handle)\n\n"
        "    return render_template(\n"
        "        'experiments.html',\n"
        "        experiments=experiments_data,\n"
        "        best_models=best_models,\n"
        "    )\n\n"
    )

    text = text[:start] + route + text[end:]

    if 'app.config["GOOGLE_MAPS_API_KEY"]' not in text:
        anchor = (
            'app.config["PERMANENT_SESSION_LIFETIME"] = '
            'timedelta(minutes=30)'
        )

        if anchor in text:
            text = text.replace(
                anchor,
                anchor
                + '\n'
                + 'app.config["GOOGLE_MAPS_API_KEY"] = '
                  'os.environ.get("GOOGLE_MAPS_API_KEY", "")',
                1,
            )

    if "register_admin_audit_hooks" not in text:
        text = text.replace(
            "CORS(app)",
            "CORS(app)\n\n"
            "from app.services.audit_hooks import "
            "register_admin_audit_hooks\n"
            "register_admin_audit_hooks(app)",
            1,
        )

    path.write_text(text, encoding="utf-8")


def patch_controller_registration():
    path = ROOT / "app" / "controllers" / "__init__.py"
    backup("app/controllers/__init__.py")
    text = path.read_text(encoding="utf-8")

    if "from .map_controller import map_bp" not in text:
        text = text.replace(
            "from .what_if_controller import what_if_bp",
            "from .what_if_controller import what_if_bp\n"
            "from .map_controller import map_bp",
            1,
        )

    if "app.register_blueprint(map_bp)" not in text:
        text = text.replace(
            "app.register_blueprint(what_if_bp)",
            "app.register_blueprint(what_if_bp)\n"
            "app.register_blueprint(map_bp)",
            1,
        )

    path.write_text(text, encoding="utf-8")


def patch_audit_template():
    path = ROOT / "app" / "views" / "admin_audit.html"
    backup("app/views/admin_audit.html")
    text = path.read_text(encoding="utf-8")

    text = text.replace(
        "log.timestamp.strftime",
        "log.created_at.strftime",
    )

    if "What belongs in an audit log?" not in text:
        marker = '<h2><i class="fas fa-list"'

        if marker in text:
            explanation = (
                '<div class="admin-card" '
                'style="margin-bottom:16px;padding:16px;">'
                "<h3>What belongs in an audit log?</h3>"
                "<p>Audit entries record privileged or security-relevant "
                "admin actions. Normal property browsing remains activity data."
                "</p></div>\n"
            )

            text = text.replace(
                marker,
                explanation + marker,
                1,
            )

    path.write_text(text, encoding="utf-8")


def patch_admin_dashboard():
    path = ROOT / "app" / "views" / "admin_dashboard.html"
    backup("app/views/admin_dashboard.html")
    text = path.read_text(encoding="utf-8")

    text = re.sub(
        r"\\s*<link[^>]+leaflet[^>]+>\\s*",
        "\n",
        text,
        flags=re.I,
    )

    text = re.sub(
        r"\\s*<script[^>]+leaflet[^>]+></script>\\s*",
        "\n",
        text,
        flags=re.I,
    )

    text = re.sub(
        r"backgroundColor:\s*\\[[^\\]]*'#4f46e5'[^\\]]*\\]",
        "backgroundColor: ['#2F6F66','#3F6D8F','#B85C38','#B68B2E']",
        text,
        count=3,
    )

    if 'class="admin-tool-links"' not in text:
        links = (
            '<div class="admin-tool-links">\n'
            '<a href="/dashboard"><strong>Property Valuation</strong>'
            '<span>Run the normal prediction workflow.</span></a>\n'
            '<a href="/comparables"><strong>Comparables</strong>'
            '<span>Review comparable properties.</span></a>\n'
            '<a href="/what-if"><strong>What-If Analysis</strong>'
            '<span>Test property scenarios.</span></a>\n'
            '<a href="/map"><strong>Location Map</strong>'
            '<span>Search properties by city and area.</span></a>\n'
            '<a href="/market-intelligence"><strong>Market Intelligence</strong>'
            '<span>Review city and property-type data.</span></a>\n'
            '<a href="/model-performance"><strong>Model Performance</strong>'
            '<span>Review model metrics.</span></a>\n'
            '<a href="/experiments"><strong>Training Experiments</strong>'
            '<span>Review A/B/C results.</span></a>\n'
            '<a href="/bulk-valuation"><strong>Bulk Valuation</strong>'
            '<span>Run CSV valuations as admin.</span></a>\n'
            "</div>\n"
        )

        marker = '<div class="content-header">'

        if marker in text:
            text = text.replace(
                marker,
                links + marker,
                1,
            )

    path.write_text(text, encoding="utf-8")


def main():
    required = [
        "app/static/css/ui_overhaul.css",
        "app/static/js/propwise_maps.js",
        "app/controllers/map_controller.py",
        "app/services/experiment_discovery.py",
        "app/services/audit_hooks.py",
        "app/views/map.html",
    ]

    for rel in required:
        if not (ROOT / rel).exists():
            raise RuntimeError(
                "Missing packaged file: " + rel
            )

    ensure_css_links()
    patch_dashboard()
    patch_model_performance()
    patch_market_intelligence()
    patch_experiments_route()
    patch_controller_registration()
    patch_audit_template()
    patch_admin_dashboard()

    env = ROOT / ".env.example"

    if not env.exists():
        env.write_text(
            "DATABASE_URL=postgresql+psycopg2://propwise:change_me@localhost:5432/propwise\n"
            "SECRET_KEY=replace_with_a_long_random_secret\n"
            "FLASK_ENV=development\n"
            "GOOGLE_MAPS_API_KEY=replace_with_google_maps_browser_key\n",
            encoding="utf-8",
        )

    print("PropWise UI overhaul applied.")
    print("Backup:", BACKUP)
    print("Set GOOGLE_MAPS_API_KEY in .env before using maps.")


if __name__ == "__main__":
    main()

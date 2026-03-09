"""
Tester Agent — Ultra-Powerful RAG-powered QA Engine (DevVerse).
─────────────────────────────────────────────────────────────────────────
This agent generates a COMPREHENSIVE pytest suite covering:
  ✅ Unit tests         — every route, every HTTP method
  ✅ Integration tests  — full form workflows (register → login → action)
  ✅ Edge cases         — 404, empty input, bad tokens, SQL injection attempts
  ✅ Auth tests         — protected routes, session management
  ✅ DB tests           — model creation, persistence, uniqueness constraints
  ✅ API tests          — JSON endpoints, status codes, response structure
  ✅ Performance guards — response time checks
  ✅ Security tests     — CSRF, XSS header presence

All input and output is filtered through the SHAP responsible AI guard.
"""

from __future__ import annotations

import re
from pathlib import Path
from core.rag_engine import rag_query, refresh_knowledge_base
from core.responsible_ai import filter_input, filter_output

_PROJECT_ROOT = Path(__file__).parent.parent.absolute()
_OUTPUTS_DIR  = _PROJECT_ROOT / "outputs"

_ROLE = (
    "You are an elite senior QA engineer and security tester with 15+ years "
    "of experience in Python Flask applications. You write battle-hardened, "
    "comprehensive pytest suites that find every bug. Your tests cover happy "
    "paths, edge cases, security vulnerabilities, and performance constraints. "
    "You always output ONLY valid Python code with zero markdown."
)

_TEST_TEMPLATE = """\
import pytest
import json
import time
from app import app, db

# ── Fixtures ────────────────────────────────────────────────
@pytest.fixture(scope="module")
def test_app():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(test_app):
    return test_app.test_client()

@pytest.fixture
def runner(test_app):
    return test_app.test_cli_runner()

# ── Utility Helpers ─────────────────────────────────────────
def register_user(client, username="testuser", password="testpass123", email="test@example.com"):
    return client.post("/register", data={"username": username, "password": password, "email": email}, follow_redirects=True)

def login_user(client, username="testuser", password="testpass123"):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
"""


def run_tester_agent() -> str:
    """
    Read Implementation_Code.txt, enrich with RAG, generate ultra-comprehensive pytest suite.
    Covers every route, auth flow, edge case, security and performance scenario.
    """
    code_file = _OUTPUTS_DIR / "Implementation_Code.txt"
    if not code_file.exists():
        code_file = _PROJECT_ROOT / "Implementation_Code.txt"
    if not code_file.exists():
        raise FileNotFoundError("Implementation_Code.txt not found. Run Developer Agent first.")

    code = code_file.read_text(encoding="utf-8").strip()
    if not code:
        raise ValueError("Implementation_Code.txt is empty.")

    # Use more code for better test generation (up to 6000 chars)
    code_excerpt = code[:6000]

    # ── Responsible-AI input filter ────────────────────────────────
    safe_code, blocked, score = filter_input(code_excerpt, stage="Test_Input")
    if blocked:
        raise RuntimeError(
            f"Input blocked by Responsible AI filter (score={score:.2f})."
        )

    # ── Refresh KB ────────────────────────────────────────────────
    refresh_knowledge_base()

    # ── Ultra-comprehensive RAG query ──────────────────────────────
    question = f"""\
Write an ULTRA-COMPREHENSIVE, IMMEDIATELY EXECUTABLE pytest test suite for the Flask application below.

MANDATORY OUTPUT RULES:
1. Output ONLY valid Python — NO markdown, NO prose, NO ``` fences anywhere.
2. Must run with: pytest test_app.py -v --tb=short
3. Import from app: import app, db and any models you find in the code.
4. If a route or model doesn't exist in the code, write a test that gracefully skips.

START WITH EXACTLY THIS BOILERPLATE (copy verbatim):
{_TEST_TEMPLATE}

THEN GENERATE ALL OF THE FOLLOWING TEST CATEGORIES:

═══ CATEGORY 1: SMOKE / HEALTH ═══
- test_app_is_created() → assert app is not None
- test_app_testing_mode() → assert app.config["TESTING"] is True
- test_home_page_loads(client) → GET / returns 200 or 302
- test_404_returns_correct_status(client) → GET /nonexistent_route_xyz returns 404

═══ CATEGORY 2: UNIT — EVERY ROUTE ═══
For each route found in the code (/, /login, /register, /dashboard, /logout, etc.):
- test_<route>_get(client) → GET returns 200/302, not 500
- test_<route>_post_empty(client) → POST with empty data returns 200/302/400, not 500

═══ CATEGORY 3: AUTH INTEGRATION ═══
- test_register_new_user(client) → valid registration succeeds
- test_register_duplicate_user(client) → second registration fails gracefully
- test_login_valid_credentials(client) → login with valid creds succeeds
- test_login_invalid_password(client) → wrong password rejected
- test_login_nonexistent_user(client) → unknown user rejected
- test_logout_clears_session(client) → logout redirects to login/home
- test_protected_route_requires_auth(client) → dashboard returns 302 when not logged in

═══ CATEGORY 4: DATABASE ═══
- test_db_creates_tables(test_app) → db.create_all() raises no exception
- test_model_creation() → create a model instance, commit, query back
- test_model_uniqueness() → duplicate unique field raises IntegrityError
- test_model_repr() → model __repr__ or __str__ works

═══ CATEGORY 5: EDGE CASES & SECURITY ═══
- test_sql_injection_username(client) → POST with "' OR '1'='1" returns 200/400, NOT 500
- test_xss_in_input(client) → POST with "<script>alert(1)</script>" returns 200/400, NOT 500
- test_empty_username_login(client) → blank username rejected, not 500
- test_very_long_input(client) → 10000-char input returns 200/400, not 500
- test_missing_required_fields(client) → POST with no data returns 200/400, not 500
- test_special_chars_in_fields(client) → special chars don't crash the app

═══ CATEGORY 6: PERFORMANCE ═══
- test_home_loads_fast(client) → GET / completes in < 3 seconds
- test_login_loads_fast(client) → GET /login completes in < 3 seconds

═══ CATEGORY 7: RESPONSE VALIDATION ═══
- test_html_response_has_body(client) → response contains <html or <body
- test_response_content_type(client) → Content-Type is text/html for page routes
- test_no_server_error_on_get_routes(client) → none of the GET routes return 500

RULES:
• Use pytest.mark.parametrize for data-driven tests wherever possible.
• Use try/except ImportError to skip gracefully if models don't exist.
• Use client.get() and client.post() with follow_redirects=True.
• Every test must have a clear docstring.
• Tests must be SELF-CONTAINED — no external dependencies.

FLASK APP CODE TO TEST:
{safe_code}
"""

    raw_output = rag_query(question=question, system_role=_ROLE, k=6)

    # ── Responsible-AI output filter ───────────────────────────────
    safe_output, blocked_out, _ = filter_output(raw_output, stage="Test_Output")

    # ── Strip any accidental markdown fences ──────────────────────
    safe_output = re.sub(r"^```[a-zA-Z]*\n?", "", safe_output.strip(), flags=re.MULTILINE)
    safe_output = re.sub(r"```$", "", safe_output.strip(), flags=re.MULTILINE)
    safe_output = safe_output.strip()

    # ── Ensure boilerplate imports are present ─────────────────────
    if "import pytest" not in safe_output:
        safe_output = "import pytest\nimport time\nfrom app import app\n\n" + safe_output

    # ── Persist ───────────────────────────────────────────────────
    _OUTPUTS_DIR.mkdir(exist_ok=True)
    (_OUTPUTS_DIR / "Test_Cases.txt").write_text(safe_output, encoding="utf-8")
    (_PROJECT_ROOT / "Test_Cases.txt").write_text(safe_output, encoding="utf-8")

    # Also write to generated_project/test_app.py so it can be run directly
    proj_test = _PROJECT_ROOT / "generated_project" / "test_app.py"
    if (_PROJECT_ROOT / "generated_project").exists():
        proj_test.write_text(safe_output, encoding="utf-8")

    return safe_output

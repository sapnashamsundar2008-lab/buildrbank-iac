"""
Does the server work?

Every test here runs with fake keys and no internet. That is deliberate:
these run on every push, in public, on a machine that is not yours. A test
that needs a real key is a test that cannot run safely in public.

WHAT WE ARE NOT TESTING
-----------------------
Whether the agent gives good answers. You cannot unit-test a model's words -
the same question can get two different replies and both be right. So we
test the plumbing: the server starts, the page is served, the procedures
load, bad input is refused. Whether the answers are any good is what
Langfuse is for, and that is a different week.
"""
from fastapi.testclient import TestClient

from app.api import api

# No `with` here, on purpose. TestClient(api) used plainly does not run the
# startup hook, so the agent is never built and no database is contacted.
# `with TestClient(api)` would start it - and fail, because our keys are fake.
client = TestClient(api)


def test_the_page_is_served():
    """GET / returns the chat page."""
    r = client.get("/")
    assert r.status_code == 200
    assert "<title>" in r.text


def test_the_header_reads_support_console():
    """The top bar says 'Support Console'.

    This is the test you are going to break today, and that is the point.
    Change that text in app/index.html and this goes red - because a test is
    just a decision someone wrote down. When you change the decision on
    purpose, you change the test too, in the same commit.

    Note how exact this is. The first version of this test looked for
    "Support Console" anywhere in the page, and it stayed green when the
    header changed - because the same words also sit in the <title>. A test
    that cannot fail is worse than no test, because it tells you nothing
    while looking like it tells you something.
    """
    r = client.get("/")
    assert "<small>Sapna's Console</small>" in r.text


def test_health_names_the_models():
    """/health reports what the server is configured to use."""
    body = client.get("/health").json()
    assert body["answer_model"]
    assert body["router_model"]
    assert body["embed_model"]


def test_health_leaks_no_keys():
    """/health is a public address. Nothing secret may appear in it."""
    body = client.get("/health").json()
    assert "test-key-not-real" not in str(body)


def test_the_procedures_load():
    """/sops lists the agent's procedures, each with steps."""
    sops = client.get("/sops").json()
    assert sops, "no procedures loaded at all"
    for name, spec in sops.items():
        assert spec["steps"], f"{name} has no steps"


def test_chat_refuses_an_empty_message():
    """An empty message is rejected before it reaches the agent.

    422, not 500. FastAPI checks the shape of the request first, so no model
    is ever called - which is why this test is safe to run with fake keys.
    """
    r = client.post("/chat", json={"message": ""})
    assert r.status_code == 422

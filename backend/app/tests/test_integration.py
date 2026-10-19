# ==============================================================================
# CampusGPT Backend — Integration Tests (API + database + RAG with fake AI)
# ==============================================================================
import json

from app.models.document import Document, DocumentChunk
from app.rag.retriever import VectorRetriever
from app.tests.conftest import fake_embedding

HOSTEL_POLICY = (
    "# Hostel Rules\n\n"
    "The hostel curfew is 9:30 PM on all days. "
    "Visitors are allowed in the hostel lounge between 4 PM and 6 PM."
)


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.split("\n") if ": " in line)
        if "event" in lines:
            events.append((lines["event"], json.loads(lines["data"])))
    return events


# ------------------------------------------------------------------------------
# Conversation isolation
# ------------------------------------------------------------------------------
async def test_users_cannot_see_or_use_each_others_conversations(make_client, fake_ai):
    alice, bob = await make_client(), await make_client()
    conversation = (await alice.post("/api/v1/conversations", json={"title": "Alice's chat"})).json()
    url = f"/api/v1/conversations/{conversation['id']}"

    assert (await bob.get(url)).status_code == 404
    assert (await bob.patch(url, json={"title": "hijacked"})).status_code == 404
    assert (await bob.delete(url)).status_code == 404
    assert (await bob.post(f"{url}/messages", json={"content": "hi", "stream": False})).status_code == 404
    bob_list = (await bob.get("/api/v1/conversations")).json()["conversations"]
    assert conversation["id"] not in [c["id"] for c in bob_list]

    # Alice still has it, untouched
    assert (await alice.get(url)).json()["title"] == "Alice's chat"


# ------------------------------------------------------------------------------
# Upload -> processing -> answer with citations
# ------------------------------------------------------------------------------
async def test_uploaded_document_is_processed_and_used_in_streamed_answer(make_client, fake_ai, test_session):
    student = await make_client()

    upload = await student.post(
        "/api/v1/documents/upload",
        files={"file": ("hostel.md", HOSTEL_POLICY.encode(), "text/markdown")},
    )
    assert upload.status_code == 201, upload.text
    assert upload.json()["visibility"] == "private"

    # The background task has run by the time the test client returns
    document = (await student.get(f"/api/v1/documents/{upload.json()['id']}")).json()
    assert document["status"] == "ready"
    assert document["chunk_count"] >= 1

    conversation = (await student.post("/api/v1/conversations", json={})).json()
    response = await student.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={"content": "What time is the hostel curfew?", "stream": True},
    )
    assert response.status_code == 200
    events = parse_sse(response.text)
    names = [name for name, _ in events]
    assert names[0] == "user_message" and names[-1] == "done"

    sources = dict(events)["sources"]
    assert [s["original_name"] for s in sources] == ["hostel.md"]
    # The model saw the full chunk text, including the curfew sentence
    assert "9:30 PM" in fake_ai.prompts[-1]

    # Both turns were saved, with sources and token usage on the answer.
    # (The test shares one DB session across requests; drop its cached copies.)
    test_session.expire_all()
    saved = (await student.get(f"/api/v1/conversations/{conversation['id']}")).json()["messages"]
    assert [m["role"] for m in saved] == ["user", "assistant"]
    assert saved[1]["content"].strip() == fake_ai.reply
    assert saved[1]["tokens_used"] == 42
    assert saved[1]["sources"][0]["original_name"] == "hostel.md"


async def test_invalid_uploads_are_rejected(make_client, fake_ai):
    student = await make_client()
    bad_type = await student.post(
        "/api/v1/documents/upload", files={"file": ("run.exe", b"MZ...", "application/octet-stream")}
    )
    wrong_extension = await student.post(
        "/api/v1/documents/upload", files={"file": ("notes.exe", b"text", "text/plain")}
    )
    assert bad_type.status_code == 400
    assert wrong_extension.status_code == 400


async def test_markdown_sent_without_a_type_is_accepted(make_client, fake_ai):
    student = await make_client()
    response = await student.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.md", b"# Notes\n\nSome notes.", "application/octet-stream")},
    )
    assert response.status_code == 201, response.text
    assert response.json()["mime_type"] == "text/markdown"


# ------------------------------------------------------------------------------
# Document visibility
# ------------------------------------------------------------------------------
async def test_private_documents_are_only_searchable_by_their_owner(make_client, fake_ai, test_session):
    alice, bob = await make_client(), await make_client()

    async def add_document(name, text, visibility, owner=None):
        document = Document(
            filename=f"{name}.txt", original_name=name, mime_type="text/plain", size_bytes=len(text),
            uploaded_by=owner, status="ready", visibility=visibility,
        )
        test_session.add(document)
        await test_session.flush()
        test_session.add(DocumentChunk(
            document_id=document.id, content=text, embedding=fake_embedding(text),
            chunk_index=0, chunk_metadata={},
        ))
        await test_session.flush()

    await add_document("campus-exam-rules", "exam hall rules for every student", "public")
    await add_document("alice-exam-notes", "exam hall rules notes by alice", "private", owner=alice.user_id)

    query = fake_embedding("exam hall rules")
    retriever = VectorRetriever(test_session)

    async def visible_to(user_id):
        hits = await retriever.search(query, user_id=user_id, similarity_threshold=0.1)
        return {hit.chunk.document.original_name for hit in hits}

    assert await visible_to(alice.user_id) == {"campus-exam-rules", "alice-exam-notes"}
    assert await visible_to(bob.user_id) == {"campus-exam-rules"}
    assert await visible_to(None) == {"campus-exam-rules"}


async def test_only_admins_can_share_documents_with_everyone(make_client, fake_ai):
    student, admin = await make_client(), await make_client(admin=True)
    file = {"file": ("calendar.md", b"# Academic calendar\n\nClasses start in July.", "text/markdown")}

    denied = await student.post("/api/v1/documents/upload", files=file, data={"share_with_everyone": "true"})
    assert denied.status_code == 403

    shared = await admin.post("/api/v1/documents/upload", files=file, data={"share_with_everyone": "true"})
    assert shared.status_code == 201
    assert shared.json()["visibility"] == "public"


# ------------------------------------------------------------------------------
# Admin access
# ------------------------------------------------------------------------------
async def test_admin_endpoints_require_admin(make_client, fake_ai):
    student, admin = await make_client(), await make_client(admin=True)
    for path in ("/api/v1/admin/documents", "/api/v1/admin/stats"):
        assert (await student.get(path)).status_code == 403
        assert (await admin.get(path)).status_code == 200


async def test_users_cannot_delete_other_users_documents_but_admins_can(make_client, fake_ai):
    alice, bob, admin = await make_client(), await make_client(), await make_client(admin=True)
    upload = await alice.post(
        "/api/v1/documents/upload", files={"file": ("mine.md", b"# Mine\n\nPrivate notes.", "text/markdown")}
    )
    url = f"/api/v1/documents/{upload.json()['id']}"

    assert (await bob.get(url)).status_code == 404
    assert (await bob.delete(url)).status_code == 404
    assert (await admin.delete(url)).status_code == 204
    assert (await alice.get(url)).status_code == 404

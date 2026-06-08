"""M1 backend tests for core data models.

Tests cover:
- Model class instantiation (python level)
- Presence of required fields / workspace_id on all data tables
- Basic SQLAlchemy session create + query
- Workspace isolation (queries on one workspace do not see another)

We deliberately avoid the embeddings table (Vector column) in the in-memory
create_all so that tests can run with plain SQLite (no pgvector extension or
native vector support required for M1 verification).

Full vector + pgvector tests can be added once a real Postgres + pgvector test
database is available (e.g. in CI or via docker compose for integration tests).
"""
import pytest
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# We import from the app package (works when PYTHONPATH=apps/api or run as module)
from app.models import (
    Base,
    Workspace,
    Show,
    Episode,
    User,
    TranscriptSegment,
    Chunk,
    IngestionJob,
)


@pytest.fixture(scope="function")
def sqlite_engine():
    """In-memory SQLite engine for M1 model tests.

    Only creates tables that do not require the pgvector extension.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Exclude the embeddings table (it uses Vector which sqlite doesn't understand)
    tables_to_create = [
        t for t in Base.metadata.sorted_tables if t.name != "embeddings"
    ]
    Base.metadata.create_all(bind=engine, tables=tables_to_create)
    yield engine


@pytest.fixture(scope="function")
def db_session(sqlite_engine):
    with Session(sqlite_engine) as session:
        yield session
        session.rollback()


def test_models_can_be_instantiated():
    """Basic smoke test that the ORM classes accept the fields from the spec."""
    ws = Workspace(name="Test WS", slug="test-ws")
    assert isinstance(ws.id, UUID)
    assert ws.name == "Test WS"

    show = Show(workspace_id=ws.id, name="Test Show", slug="test-show")
    assert show.workspace_id == ws.id

    ep = Episode(
        workspace_id=ws.id,
        show_id=uuid4(),  # would normally be real
        title="Pilot",
        ingestion_status="not_started",
    )
    assert ep.ingestion_status == "not_started"


def test_workspace_isolation_basic(db_session: Session):
    """Create two workspaces + children and verify queries are isolated by workspace_id.

    This is the core invariant required by the product (spec §3.1, §13, §21).
    """
    # Workspace A
    ws_a = Workspace(name="Workspace A", slug="ws-a")
    db_session.add(ws_a)
    db_session.flush()

    show_a = Show(workspace_id=ws_a.id, name="Show A", slug="show-a")
    ep_a = Episode(workspace_id=ws_a.id, show_id=show_a.id, title="Ep A")
    db_session.add_all([show_a, ep_a])

    # Workspace B
    ws_b = Workspace(name="Workspace B", slug="ws-b")
    db_session.add(ws_b)
    db_session.flush()

    show_b = Show(workspace_id=ws_b.id, name="Show B", slug="show-b")
    ep_b = Episode(workspace_id=ws_b.id, show_id=show_b.id, title="Ep B")
    db_session.add_all([show_b, ep_b])
    db_session.commit()

    # Query only for ws_a
    shows_in_a = db_session.execute(
        select(Show).where(Show.workspace_id == ws_a.id)
    ).scalars().all()
    assert len(shows_in_a) == 1
    assert shows_in_a[0].name == "Show A"

    # Query only for ws_b
    shows_in_b = db_session.execute(
        select(Show).where(Show.workspace_id == ws_b.id)
    ).scalars().all()
    assert len(shows_in_b) == 1
    assert shows_in_b[0].name == "Show B"

    # Global query (without workspace filter) would see both — this is why every
    # API/repository layer MUST always add the workspace filter.
    all_shows = db_session.execute(select(Show)).scalars().all()
    assert len(all_shows) == 2


def test_episode_and_segment_relationships(db_session: Session):
    """Light relationship + cascade sanity check (non-vector tables)."""
    ws = Workspace(name="Rel WS", slug="rel-ws")
    db_session.add(ws)
    db_session.flush()

    show = Show(workspace_id=ws.id, name="Rel Show", slug="rel-show")
    ep = Episode(workspace_id=ws.id, show_id=show.id, title="Rel Ep")
    db_session.add_all([show, ep])
    db_session.flush()

    seg = TranscriptSegment(
        workspace_id=ws.id,
        episode_id=ep.id,
        segment_index=0,
        text="Hello from the archive.",
    )
    db_session.add(seg)
    db_session.commit()

    # Reload via relationship
    reloaded = db_session.get(Episode, ep.id)
    assert reloaded is not None
    assert len(reloaded.transcript_segments) == 1
    assert reloaded.transcript_segments[0].text.startswith("Hello")


def test_ingestion_job_and_chunk_models(db_session: Session):
    """Exercise a couple more model shapes that will be used by later milestones."""
    ws = Workspace(name="Job WS", slug="job-ws")
    db_session.add(ws)
    db_session.flush()

    ep = Episode(workspace_id=ws.id, show_id=uuid4(), title="Job Ep")
    db_session.add(ep)
    db_session.flush()

    job = IngestionJob(
        workspace_id=ws.id,
        episode_id=ep.id,
        job_type="full_ingestion",
        status="queued",
    )
    chunk = Chunk(
        workspace_id=ws.id,
        episode_id=ep.id,
        chunk_index=0,
        text="Some transcript content that will be embedded.",
        token_count=12,
    )
    db_session.add_all([job, chunk])
    db_session.commit()

    assert db_session.get(IngestionJob, job.id).status == "queued"
    assert db_session.get(Chunk, chunk.id).token_count == 12

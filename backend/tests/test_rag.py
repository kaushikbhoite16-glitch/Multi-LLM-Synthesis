import pytest
import os
import asyncio
from app.rag.embeddings import embedding_service
from app.rag.chunking import SemanticChunker
from app.rag.vector_store import vector_store, GENERAL_COLLECTION, ACADEMIC_COLLECTION, DYNAMIC_WEB_COLLECTION
from app.rag.bm25_retriever import bm25_retriever
from app.rag.fusion import reciprocal_rank_fusion, deduplicate_chunks, rerank_and_fuse
from app.rag.claim_extractor import claim_extractor
from app.rag.evidence_verifier import evidence_verifier
from app.rag.evidence_scorer import evidence_scorer
from app.rag.sources.general_kb import general_kb
from app.rag.sources.academic_kb import academic_kb
from app.rag.sources.dynamic_web import dynamic_web
from app.rag.seed_data import ensure_seed_data
from app.services.pipeline import PipelineOrchestrator
from app.schemas.pydantic_models import PipelineRunRequest

@pytest.fixture(scope="module", autouse=True)
def setup_rag_seed():
    """Ensures seed data is loaded into ChromaDB collections before tests."""
    ensure_seed_data()

def test_semantic_chunker():
    chunker = SemanticChunker(chunk_size=50, chunk_overlap=10)
    text = (
        "# Heading 1\n\n"
        "This is paragraph one with some detailed technical content about computer algorithms. "
        "It discusses sorting algorithms like quicksort and mergesort.\n\n"
        "## Heading 2\n\n"
        "This is paragraph two focusing on graph traversal methods like breadth-first search "
        "and depth-first search in modern network topologies."
    )
    chunks = chunker.chunk_document("test_doc_1", text, {"title": "Algorithm Overview"})
    assert len(chunks) >= 1
    assert "document_id" in chunks[0]["metadata"]
    assert chunks[0]["metadata"]["document_id"] == "test_doc_1"
    assert "chunk_id" in chunks[0]

def test_embedding_service_cosine_similarity():
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [1.0, 0.0, 0.0]
    vec_c = [0.0, 1.0, 0.0]

    assert abs(embedding_service.cosine_similarity(vec_a, vec_b) - 1.0) < 1e-4
    assert abs(embedding_service.cosine_similarity(vec_a, vec_c) - 0.0) < 1e-4

    # Real embeddings
    emb1 = embedding_service.embed_query("computer science programming")
    emb2 = embedding_service.embed_query("software development coding")
    emb3 = embedding_service.embed_query("banana strawberry fruit smoothie")

    sim_related = embedding_service.cosine_similarity(emb1, emb2)
    sim_unrelated = embedding_service.cosine_similarity(emb1, emb3)
    assert sim_related > sim_unrelated

def test_bm25_retriever():
    chunks = [
        {"chunk_id": "c1", "text": "Python supports for loops and while loops for iteration."},
        {"chunk_id": "c2", "text": "Operating systems use virtual memory and paging mechanisms."},
        {"chunk_id": "c3", "text": "TCP is a reliable transport layer protocol with a three-way handshake."}
    ]
    results = bm25_retriever.search_dynamic_chunks("for loops python", chunks, top_k=2)
    assert len(results) >= 1
    assert results[0]["chunk_id"] == "c1"
    assert results[0]["score"] > 0.0

def test_reciprocal_rank_fusion_and_deduplication():
    dense_list = [
        {"chunk_id": "c1", "text": "For loops in python execute iteratively.", "score": 0.95},
        {"chunk_id": "c2", "text": "While loops execute conditionally.", "score": 0.85}
    ]
    sparse_list = [
        {"chunk_id": "c1", "text": "For loops in python execute iteratively.", "score": 0.90},
        {"chunk_id": "c3", "text": "Iteration constructs include loops.", "score": 0.70}
    ]

    fused = reciprocal_rank_fusion([dense_list, sparse_list], weights=[0.6, 0.4])
    assert len(fused) == 3
    # c1 appears in both lists, so it must have the highest accumulated RRF score
    assert fused[0]["chunk_id"] == "c1"

    # Deduplication test
    dup_candidates = [
        {"chunk_id": "c1", "text": "For loops in python execute iteratively over sequences."},
        {"chunk_id": "c2", "text": "For loops in python execute iteratively over sequences."}
    ]
    deduped = deduplicate_chunks(dup_candidates)
    assert len(deduped) == 1

def test_claim_extractor():
    text = (
        "Here is the explanation for you.\n\n"
        "A for loop is a fundamental control flow construct. "
        "It iterates over collections and ranges. "
        "In Python, the syntax is for item in iterable. "
        "Hope this helps you understand!"
    )
    claims = claim_extractor.extract_claims(text)
    assert len(claims) >= 2
    # Ensure conversational filler was stripped
    assert not any("here is the explanation" in c.lower() for c in claims)
    assert not any("hope this helps" in c.lower() for c in claims)

def test_evidence_verifier_and_scorer():
    evidence = [
        {
            "citation_id": "[1]",
            "title": "Programming Fundamentals",
            "text": "A for loop is a control flow statement used to repeatedly execute a block of code and iterate over elements in a sequence.",
            "source_type": "general"
        }
    ]

    claims = [
        "A for loop is a control flow statement used to execute code and iterate over elements.",
        "Virtual memory uses page tables and TLBs to map virtual addresses."
    ]

    verified = evidence_verifier.verify_claims(claims, evidence)
    assert len(verified) == 2
    assert verified[0]["status"] == "SUPPORTED"
    assert "[1]" in verified[0]["citations"]
    # Virtual memory claim is not supported by the for loop evidence
    assert verified[1]["status"] in ("INSUFFICIENT_EVIDENCE", "CONTRADICTED")

def test_evidence_scorer_formula():
    evidence = [
        {
            "citation_id": "[1]",
            "title": "Programming: For Loops",
            "text": "A for loop repeatedly executes code across sequences and ranges.",
            "source_type": "general"
        }
    ]

    query = "what is for loop"
    good_text = "A for loop is a programming construct used to iterate over a sequence of items."
    bad_text = "Virtual memory decouples an application's logical address space from physical RAM."

    eval_good = evidence_scorer.evaluate_response(query, good_text, "model-a", "r1", evidence)
    eval_bad = evidence_scorer.evaluate_response(query, bad_text, "model-b", "r2", evidence)

    assert eval_good["final_score"] > eval_bad["final_score"]
    assert eval_good["breakdown"]["relevance"] > eval_bad["breakdown"]["relevance"]

@pytest.mark.asyncio
async def test_hybrid_pipeline_execution():
    orchestrator = PipelineOrchestrator()
    req = PipelineRunRequest(
        query="what is for loop",
        execution_mode="simulation",
        enable_rag=True
    )
    res = await orchestrator.execute_pipeline(req)

    assert res.query_text == "what is for loop"
    assert res.retrieved_evidence is not None
    assert len(res.retrieved_evidence) >= 1
    # Check that retrieved evidence is relevant to for loops
    assert any("loop" in e["title"].lower() or "loop" in e["text"].lower() for e in res.retrieved_evidence)
    # Check that synthesis has references and verified claims
    assert res.synthesis is not None
    assert res.synthesis.final_response is not None
    assert len(res.ranking) > 0


def test_cross_encoder_reranker():
    from app.rag.cross_encoder import cross_encoder
    query = "Operating System Virtual Memory Paging"
    candidate_chunks = [
        {"chunk_id": "c1", "text": "This text discusses recipe ingredients for pasta.", "score": 0.4},
        {"chunk_id": "c2", "text": "Virtual memory is an OS abstraction using page tables and TLBs.", "score": 0.8},
        {"chunk_id": "c3", "text": "Computer networks use IP addresses and routing protocols.", "score": 0.5}
    ]
    reranked = cross_encoder.rerank(query, candidate_chunks, top_k=2)
    assert len(reranked) == 2
    # Chunk c2 must be ranked #1 by cross-encoder
    assert reranked[0]["chunk_id"] == "c2"
    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]


def test_document_loader_pdf_txt_html(tmp_path):
    from app.rag.document_loader import document_loader
    # Test TXT
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Linear search is O(n), while binary search is O(log n).", encoding="utf-8")
    loaded_txt = document_loader.load_file(str(txt_file))
    assert "binary search" in loaded_txt["text"]
    assert "content_hash" in loaded_txt["metadata"]

    # Test HTML
    html_file = tmp_path / "test.html"
    html_file.write_text("<html><head><title>Data Structures</title></head><body><h1>Stacks and Queues</h1><p>Stacks are LIFO.</p></body></html>", encoding="utf-8")
    loaded_html = document_loader.load_file(str(html_file))
    assert "Stacks are LIFO" in loaded_html["text"]
    assert loaded_html["metadata"]["title"] == "Data Structures"


@pytest.mark.asyncio
async def test_all_four_academic_providers():
    # Test all 4 academic provider interfaces
    arxiv_res = await academic_kb.fetch_and_ingest_arxiv("quantum computing algorithms", max_results=1)
    openalex_res = await academic_kb.fetch_and_ingest_openalex("deep neural networks", max_results=1)
    crossref_res = await academic_kb.fetch_and_ingest_crossref("graph algorithms", max_results=1)
    s2_res = await academic_kb.fetch_and_ingest_semantic_scholar("attention mechanism transformer", max_results=1)

    assert isinstance(arxiv_res, list)
    assert isinstance(openalex_res, list)
    assert isinstance(crossref_res, list)
    assert isinstance(s2_res, list)


@pytest.mark.asyncio
async def test_document_persistence_and_chroma_sync():
    from app.models.entities import Document as DocumentEntity, DocumentChunk as DocumentChunkEntity
    from app.database.session import engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    test_doc_id = "doc_test_sync_001"

    # Ensure cleanup
    vector_store.delete_document_chunks(GENERAL_COLLECTION, test_doc_id)

    # 1. Ingest to ChromaDB
    chunks = [
        {"chunk_id": f"{test_doc_id}_chunk_001", "text": "Test passage content for synchronized persistence.", "metadata": {"document_id": test_doc_id, "chunk_index": 1}}
    ]
    vector_store.add_chunks(GENERAL_COLLECTION, [c["chunk_id"] for c in chunks], [c["text"] for c in chunks], [c["metadata"] for c in chunks])

    async with async_session() as db:
        # Clean any prior doc
        existing = await db.execute(select(DocumentEntity).where(DocumentEntity.id == test_doc_id))
        prior = existing.scalar_one_or_none()
        if prior:
            await db.delete(prior)
            await db.commit()

        # 2. Persist in Database
        doc_entity = DocumentEntity(
            id=test_doc_id,
            title="Synchronized Document Test",
            source_type="general",
            status="active"
        )
        db.add(doc_entity)
        await db.flush()

        chunk_entity = DocumentChunkEntity(
            id=f"{test_doc_id}_chunk_001",
            document_id=test_doc_id,
            chunk_index=1,
            collection_name=GENERAL_COLLECTION,
            chromadb_id=f"{test_doc_id}_chunk_001",
            text_snippet="Test passage content",
            token_count=10
        )
        db.add(chunk_entity)
        await db.commit()

        # Verify presence
        res = await db.execute(select(DocumentEntity).where(DocumentEntity.id == test_doc_id))
        assert res.scalar_one_or_none() is not None

    # Verify ChromaDB presence
    col = vector_store.get_collection(GENERAL_COLLECTION)
    before_del = col.get(ids=[f"{test_doc_id}_chunk_001"])
    assert len(before_del["ids"]) == 1

    # Synchronized Deletion
    del_count = vector_store.delete_document_chunks(GENERAL_COLLECTION, test_doc_id)
    assert del_count == 1
    after_del = col.get(ids=[f"{test_doc_id}_chunk_001"])
    assert len(after_del["ids"]) == 0



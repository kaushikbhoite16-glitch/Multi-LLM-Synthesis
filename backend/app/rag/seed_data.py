from typing import Dict, Any
from app.rag.vector_store import vector_store, GENERAL_COLLECTION, ACADEMIC_COLLECTION
from app.rag.sources.general_kb import general_kb
from app.rag.sources.academic_kb import academic_kb
from app.utils.logger import logger

GENERAL_SEED_DOCUMENTS = [
    {
        "title": "Programming Fundamentals: The For Loop and Iteration Constructs",
        "category": "programming",
        "source_url": "https://docs.python.org/3/tutorial/controlflow.html#for-statements",
        "text": """# Programming Fundamentals: The For Loop and Iteration Constructs

## What is a For Loop?
A **for loop** is a fundamental control flow statement in programming used to repeatedly execute a block of code a specific number of times or iterate over elements in a sequence (such as a list, array, tuple, string, or range).

## Mechanics of a For Loop
1. **Initialization**: A counter or iterator variable is initialized.
2. **Condition / Range**: The loop evaluates whether the iteration criteria is met (or whether more items exist in the iterable).
3. **Execution**: The loop body runs once per iteration.
4. **Step / Update**: In counter-based languages (like C, C++, and Java), the iterator increments or decrements (e.g., `i++`). In iterator-based languages (like Python), the next item from the iterator is yielded.

## Language Implementations

### Python
Python uses for loops for collection and sequence traversal:
```python
# Iterating over a range
for i in range(5):
    print(i)  # Prints 0, 1, 2, 3, 4

# Iterating over a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)
```

### C / C++ / Java
In C-family languages, a for loop typically has three parts separated by semicolons:
```c
for (int i = 0; i < 5; i++) {
    printf("%d\\n", i);
}
```

## Key Applications and Properties
- **Deterministic Iteration**: Ideal when the number of iterations is known in advance or tied to data structures.
- **Complexity**: Executing a loop of $N$ elements takes $O(N)$ linear time complexity.
- **Nested Loops**: Placing one for loop inside another achieves $O(N \\times M)$ operations, commonly used for matrix traversal.
- **Contrast with While Loops**: While loops repeat indefinitely based on a boolean condition; for loops repeat over a bounded sequence or counter.
"""
    },
    {
        "title": "Operating Systems: Virtual Memory, Paging, and Memory Management",
        "category": "operating_systems",
        "source_url": "https://en.wikipedia.org/wiki/Virtual_memory",
        "text": """# Operating Systems: Virtual Memory and Paging

## Overview of Virtual Memory
Virtual memory is an essential operating system abstraction that gives every running application the perception of having dedicated, uninterrupted access to contiguous RAM, even when physical RAM is fragmented or shared among multiple processes.

## Core Mechanisms
1. **Virtual Address Space**: Each process is granted an isolated address space mapped to physical addresses via hardware Page Tables.
2. **Paging**: Physical memory is divided into fixed-size blocks called **page frames** (typically 4 KB), and virtual memory is divided into equal-sized **pages**.
3. **Memory Management Unit (MMU)**: A dedicated hardware unit that translates virtual addresses to physical addresses at runtime.
4. **Translation Lookaside Buffer (TLB)**: A high-speed hardware cache that stores recent virtual-to-physical address translations to minimize memory access latency.
5. **Page Fault Handling**: If a process accesses a page not currently residing in physical RAM, the MMU triggers a Page Fault exception. The OS retrieves the required page from secondary storage (swap/disk) into RAM.

## Benefits
- **Process Isolation**: Prevents faulty or malicious programs from reading or corrupting the memory of other processes.
- **Overcommitting Memory**: Enables the system to run applications requiring more aggregate memory than physically installed RAM through disk paging.
"""
    },
    {
        "title": "Computer Networks: TCP vs UDP Transport Layer Protocols",
        "category": "computer_networks",
        "source_url": "https://www.ietf.org/rfc/rfc793.txt",
        "text": """# Computer Networks: TCP vs UDP Transport Protocols

## Transmission Control Protocol (TCP)
TCP (RFC 793) is a connection-oriented, reliable transport layer protocol designed to deliver byte streams across IP networks without loss or duplication.
- **3-Way Handshake**: Establishes a session using SYN, SYN-ACK, ACK.
- **Reliability**: Uses sequence numbers, positive acknowledgments (ACKs), and automatic retransmissions (ARQ).
- **Flow and Congestion Control**: Implements sliding window algorithms, slow start, and congestion avoidance.
- **Use Cases**: Web browsing (HTTP/HTTPS), file transfer (FTP), email (SMTP), SSH.

## User Datagram Protocol (UDP)
UDP (RFC 768) is a connectionless, lightweight, best-effort transport layer protocol.
- **Minimal Overhead**: 8-byte header compared to TCP's 20-60 byte header.
- **No Handshake or Guarantees**: Does not guarantee packet delivery, in-order arrival, or flow control.
- **Low Latency**: Packets are transmitted immediately without waiting for ACKs.
- **Use Cases**: Real-time video conferencing (WebRTC), online multiplayer gaming, DNS queries, VoIP.
"""
    },
    {
        "title": "Data Structures: Linked Lists, Dynamic Arrays, and Memory Layout",
        "category": "data_structures",
        "source_url": "https://en.wikipedia.org/wiki/Linked_list",
        "text": """# Data Structures: Linked Lists vs Dynamic Arrays

## Singly and Doubly Linked Lists
A linked list is a linear data structure consisting of discrete nodes where each node contains data and one or more references (pointers) to adjacent nodes.
- **Singly Linked List**: Each node points only to the next node (`next`).
- **Doubly Linked List**: Each node maintains pointers to both `next` and `prev` nodes, enabling bidirectional traversal.

## Performance Comparison
| Operation | Dynamic Array (Vector) | Linked List |
|---|---|---|
| Access by Index (Random) | $O(1)$ | $O(n)$ |
| Insertion / Deletion at Head | $O(n)$ | $O(1)$ |
| Insertion / Deletion at Tail | $O(1)$ amortized | $O(1)$ (with tail pointer) |
| Insertion in Middle (known pos) | $O(n)$ (shifting) | $O(1)$ (pointer update) |
| Cache Locality | Excellent (contiguous) | Poor (pointer chasing) |
"""
    },
    {
        "title": "Data Structures: Stacks, Queues, and FIFO/LIFO Mechanics",
        "category": "data_structures",
        "source_url": "https://en.wikipedia.org/wiki/Stack_(abstract_data_type)",
        "text": """# Data Structures: Stacks and Queues

## Stack (LIFO - Last In, First Out)
A stack is an abstract data structure where elements are added and removed from the same end, called the **top**.
- **Push**: Adds an element to the top ($O(1)$).
- **Pop**: Removes and returns the top element ($O(1)$).
- **Peek / Top**: Inspects the topmost element without removing it.
- **Applications**: Function call call-stack execution, undo mechanisms in software, syntax parsing, depth-first search (DFS).

## Queue (FIFO - First In, First Out)
A queue is an abstract data structure where elements are inserted at the **rear** (enqueue) and removed from the **front** (dequeue).
- **Enqueue**: Adds an item to the rear ($O(1)$).
- **Dequeue**: Removes the front item ($O(1)$).
- **Applications**: Operating system CPU scheduling queues, print spoolers, asynchronous message brokers (RabbitMQ/Kafka), breadth-first search (BFS).
"""
    },
    {
        "title": "Artificial Intelligence: Retrieval-Augmented Generation (RAG) Architecture",
        "category": "artificial_intelligence",
        "source_url": "https://research.ibm.com/blog/retrieval-augmented-generation-RAG",
        "text": """# Artificial Intelligence: Retrieval-Augmented Generation (RAG)

## Motivation and Definition
Retrieval-Augmented Generation (RAG) is an architectural pattern that combines parametric memory (pre-trained Large Language Model weights) with non-parametric memory (external searchable knowledge bases and vector stores).

## The Hybrid RAG Pipeline
1. **Query Processing**: The user's query is normalized and converted into both dense semantic embeddings and sparse keyword tokens.
2. **Hybrid Retrieval**:
   - **Dense Retrieval**: Employs vector embeddings (e.g., all-MiniLM-L6-v2) to capture semantic intent and conceptual similarity.
   - **Sparse Retrieval**: Uses BM25 to achieve exact lexical matches for technical keywords, code tokens, and acronyms.
   - **Reciprocal Rank Fusion (RRF)**: Merges the ranked lists from dense and sparse retrievers without requiring score normalization.
3. **Reranking**: Cross-encoders or quality weighting filters candidate evidence chunks by source authority.
4. **Augmented Prompting**: Retrieved evidence chunks are injected into the LLM context window with explicit citation instructions.
5. **Synthesis & Verification**: The LLM synthesizes an authoritative answer and grounds its claims with verifiable citations.
"""
    }
]

ACADEMIC_SEED_PAPERS = [
    {
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "abstract": "Large pre-trained language models store factual knowledge in their parameters, but their ability to access and precisely manipulate knowledge is limited. We introduce RAG, a general-purpose fine-tuning recipe for retrieval-augmented generation. RAG models combine pre-trained parametric and non-parametric memory for language generation, achieving state-of-the-art results on open-domain question answering benchmarks.",
        "authors": "Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, Douwe Kiela",
        "year": 2020,
        "venue": "Advances in Neural Information Processing Systems (NeurIPS 2020)",
        "doi": "10.48550/arXiv.2005.11401",
        "arxiv_id": "2005.11401"
    },
    {
        "title": "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection",
        "abstract": "Despite their remarkable capabilities, large language models (LLMs) often hallucinate ungrounded responses due to relying solely on parametric knowledge. We introduce Self-Reflective Retrieval-Augmented Generation (Self-RAG), a framework that improves an LLM's quality and factuality through retrieval on demand and self-reflection. Self-RAG trains an arbitrary language model to selectively retrieve information and evaluate retrieved passages using reflection tokens.",
        "authors": "Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, Hannaneh Hajishirzi",
        "year": 2024,
        "venue": "International Conference on Learning Representations (ICLR 2024)",
        "doi": "10.48550/arXiv.2310.11511",
        "arxiv_id": "2310.11511"
    },
    {
        "title": "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena",
        "abstract": "Evaluating Large Language Model (LLM) based chat assistants is challenging due to their broad capabilities and the difficulty of defining objective ground truth. We explore the use of strong LLMs as judges to evaluate model outputs on open-ended questions. We examine agreement between LLM judges and human preferences, identifying position bias, verbosity bias, and self-enhancement bias, and propose multi-criteria grading standards.",
        "authors": "Lianmin Zheng, Wei-Lin Chiang, Hao Zhang, Siyuan Zhuang, Yonghao Zhuang, Joseph E. Gonzalez, Ion Stoica",
        "year": 2023,
        "venue": "Advances in Neural Information Processing Systems (NeurIPS 2023)",
        "doi": "10.48550/arXiv.2306.05685",
        "arxiv_id": "2306.05685"
    }
]

def ensure_seed_data(force: bool = False):
    """
    Checks if ChromaDB collections are empty; if so, populates them with foundational seed documents.
    """
    gen_count = vector_store.get_collection(GENERAL_COLLECTION).count()
    if gen_count == 0 or force:
        logger.info(f"Populating general knowledge base with {len(GENERAL_SEED_DOCUMENTS)} seed documents...")
        for doc in GENERAL_SEED_DOCUMENTS:
            try:
                general_kb.ingest_text(
                    text=doc["text"],
                    title=doc["title"],
                    category=doc["category"],
                    source_url=doc.get("source_url", "")
                )
            except Exception as e:
                logger.warning(f"Error seeding general document '{doc['title']}': {e}")

    acad_count = vector_store.get_collection(ACADEMIC_COLLECTION).count()
    if acad_count == 0 or force:
        logger.info(f"Populating academic knowledge base with {len(ACADEMIC_SEED_PAPERS)} seed papers...")
        for paper in ACADEMIC_SEED_PAPERS:
            try:
                academic_kb.ingest_paper(
                    title=paper["title"],
                    abstract=paper["abstract"],
                    authors=paper["authors"],
                    year=paper["year"],
                    venue=paper.get("venue", ""),
                    doi=paper.get("doi", ""),
                    arxiv_id=paper.get("arxiv_id", "")
                )
            except Exception as e:
                logger.warning(f"Error seeding academic paper '{paper['title']}': {e}")

    logger.info(f"Seed data verification complete. General: {vector_store.get_collection(GENERAL_COLLECTION).count()} chunks, Academic: {vector_store.get_collection(ACADEMIC_COLLECTION).count()} chunks.")

async def sync_seed_documents_to_db(db):
    """Synchronizes seed foundational documents and chunk records into PostgreSQL metadata."""
    from sqlalchemy import select
    from app.models.entities import Document as DocumentEntity, DocumentChunk as DocumentChunkEntity
    from app.rag.chunking import SemanticChunker
    chunker = SemanticChunker()

    for idx, doc in enumerate(GENERAL_SEED_DOCUMENTS, start=1):
        doc_id = f"doc_seed_gen_{idx:03d}"
        res = await db.execute(select(DocumentEntity).where(DocumentEntity.id == doc_id))
        if not res.scalar_one_or_none():
            doc_entity = DocumentEntity(
                id=doc_id,
                title=doc["title"],
                source_type="general",
                source_url=doc.get("source_url", ""),
                status="active"
            )
            db.add(doc_entity)
            await db.flush()
            chunks = chunker.chunk_document(doc_id, doc["text"], {"title": doc["title"]})
            for c_idx, c in enumerate(chunks, start=1):
                chunk_entity = DocumentChunkEntity(
                    id=f"{doc_id}_chunk_{c_idx:03d}",
                    document_id=doc_id,
                    chunk_index=c_idx,
                    collection_name=GENERAL_COLLECTION,
                    chromadb_id=f"{doc_id}_chunk_{c_idx:03d}",
                    text_snippet=c["text"][:500],
                    token_count=len(c["text"].split())
                )
                db.add(chunk_entity)

    for idx, paper in enumerate(ACADEMIC_SEED_PAPERS, start=1):
        doc_id = f"doc_seed_acad_{idx:03d}"
        res = await db.execute(select(DocumentEntity).where(DocumentEntity.id == doc_id))
        if not res.scalar_one_or_none():
            doc_entity = DocumentEntity(
                id=doc_id,
                title=paper["title"],
                source_type="academic",
                source_url=paper.get("doi", ""),
                doi=paper.get("doi", ""),
                authors=[paper.get("authors", "")],
                status="active"
            )
            db.add(doc_entity)
            await db.flush()
            chunk_entity = DocumentChunkEntity(
                id=f"{doc_id}_chunk_001",
                document_id=doc_id,
                chunk_index=1,
                collection_name=ACADEMIC_COLLECTION,
                chromadb_id=f"{doc_id}_chunk_001",
                text_snippet=paper["abstract"][:500],
                token_count=len(paper["abstract"].split())
            )
            db.add(chunk_entity)

    try:
        await db.commit()
    except Exception as e:
        logger.warning(f"Seed DB sync note: {e}")
        await db.rollback()


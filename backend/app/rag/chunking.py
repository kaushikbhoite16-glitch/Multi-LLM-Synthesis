import re
from typing import List, Dict, Any
from app.config import settings

class SemanticChunker:
    def __init__(
        self,
        chunk_size: int = settings.RAG_CHUNK_SIZE,
        chunk_overlap: int = settings.RAG_CHUNK_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        document_id: str,
        text: str,
        base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Splits text into meaningful semantic sections (by headings/paragraphs)
        and batches them into overlapping chunks bounded by chunk_size.
        """
        if not text or not text.strip():
            return []

        # Split into semantic paragraph/section units
        raw_sections = re.split(r"(?:\n\s*\n)|(?=^#{1,3}\s)", text, flags=re.MULTILINE)
        units = [s.strip() for s in raw_sections if s and s.strip()]

        if not units:
            units = [text.strip()]

        chunks = []
        current_words: List[str] = []
        current_section_title = base_metadata.get("title", "")

        for unit in units:
            # Check if this unit is a heading
            if unit.startswith("#"):
                heading_line = unit.splitlines()[0].lstrip("#").strip()
                if heading_line:
                    current_section_title = heading_line[:100]

            unit_words = unit.split()
            if not unit_words:
                continue

            # If adding this unit exceeds chunk size and we already have content:
            if len(current_words) + len(unit_words) > self.chunk_size and current_words:
                chunk_text = " ".join(current_words)
                chunk_idx = len(chunks) + 1
                chunk_id = f"{document_id}_chunk_{chunk_idx:03d}"

                meta = dict(base_metadata)
                meta.update({
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                    "chunk_index": chunk_idx,
                    "section": current_section_title,
                    "token_count": len(current_words)
                })

                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "metadata": meta
                })

                # Maintain sliding window overlap
                if self.chunk_overlap > 0 and len(current_words) > self.chunk_overlap:
                    current_words = current_words[-self.chunk_overlap:]
                else:
                    current_words = []

            # If single unit is larger than chunk_size, split by sliding window
            if len(unit_words) > self.chunk_size:
                step = self.chunk_size - self.chunk_overlap
                for i in range(0, len(unit_words), max(1, step)):
                    sub_words = unit_words[i : i + self.chunk_size]
                    if not sub_words:
                        continue
                    chunk_text = " ".join(sub_words)
                    chunk_idx = len(chunks) + 1
                    chunk_id = f"{document_id}_chunk_{chunk_idx:03d}"

                    meta = dict(base_metadata)
                    meta.update({
                        "document_id": document_id,
                        "chunk_id": chunk_id,
                        "chunk_index": chunk_idx,
                        "section": current_section_title,
                        "token_count": len(sub_words)
                    })

                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                        "metadata": meta
                    })
                current_words = []
            else:
                current_words.extend(unit_words)

        # Flush remaining words
        if current_words:
            chunk_text = " ".join(current_words)
            chunk_idx = len(chunks) + 1
            chunk_id = f"{document_id}_chunk_{chunk_idx:03d}"

            meta = dict(base_metadata)
            meta.update({
                "document_id": document_id,
                "chunk_id": chunk_id,
                "chunk_index": chunk_idx,
                "section": current_section_title,
                "token_count": len(current_words)
            })

            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "metadata": meta
            })

        return chunks

chunker = SemanticChunker()

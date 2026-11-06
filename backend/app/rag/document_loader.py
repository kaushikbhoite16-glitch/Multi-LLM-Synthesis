import os
import re
import hashlib
from typing import Dict, Any, Optional
from app.utils.logger import logger

class DocumentLoader:
    @staticmethod
    def calculate_hash(content: str) -> str:
        """Returns a hex SHA-256 hash of the content to prevent duplicate ingestion."""
        return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()

    @staticmethod
    def clean_text(text: str) -> str:
        """Cleans extracted text by normalizing whitespace while preserving code and structure."""
        if not text:
            return ""
        # Remove non-printable control characters except standard whitespace
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        # Normalize multiple spaces and tabs to single space
        text = re.sub(r"[ \t]+", " ", text)
        # Normalize excessive newlines (max 2 consecutive newlines)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()

    @classmethod
    def load_pdf(cls, file_path: str) -> Dict[str, Any]:
        """Extracts text and metadata from a PDF file using PyMuPDF (fitz) or pypdf."""
        extracted_text = []
        metadata = {
            "file_path": file_path,
            "title": os.path.basename(file_path),
            "pages": 0
        }

        # Attempt PyMuPDF (fitz) first
        try:
            import fitz
            doc = fitz.open(file_path)
            metadata["pages"] = len(doc)
            doc_meta = doc.metadata or {}
            if doc_meta.get("title"):
                metadata["title"] = doc_meta["title"]
            if doc_meta.get("author"):
                metadata["author"] = doc_meta["author"]

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    extracted_text.append(f"--- Page {page_num + 1} ---\n{text}")
            doc.close()
        except ImportError:
            # Fallback to pypdf
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                metadata["pages"] = len(reader.pages)
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        extracted_text.append(f"--- Page {page_num + 1} ---\n{text}")
            except Exception as e:
                logger.error(f"Failed to extract PDF via pypdf: {e}")
        except Exception as e:
            logger.error(f"Failed to extract PDF via PyMuPDF: {e}")

        full_content = "\n\n".join(extracted_text)
        cleaned_content = cls.clean_text(full_content)
        metadata["content_hash"] = cls.calculate_hash(cleaned_content)
        return {
            "text": cleaned_content,
            "metadata": metadata
        }

    @classmethod
    def load_html(cls, html_content: str, source_url: Optional[str] = None) -> Dict[str, Any]:
        """Extracts clean readable text from HTML markup, discarding scripts and styling."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove non-content elements
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe", "aside"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            if not title:
                h1 = soup.find("h1")
                title = h1.get_text().strip() if h1 else (source_url or "Web Document")

            text = soup.get_text(separator="\n")
            cleaned_text = cls.clean_text(text)
            
            return {
                "text": cleaned_text,
                "metadata": {
                    "title": title[:200],
                    "source_url": source_url or "",
                    "content_hash": cls.calculate_hash(cleaned_text)
                }
            }
        except Exception as e:
            logger.warning(f"HTML parsing fallback: {e}")
            cleaned_text = cls.clean_text(html_content)
            return {
                "text": cleaned_text,
                "metadata": {
                    "title": source_url or "Raw HTML Content",
                    "source_url": source_url or "",
                    "content_hash": cls.calculate_hash(cleaned_text)
                }
            }

    @classmethod
    def load_text(cls, content: str, title: str = "Text Document", source_url: Optional[str] = None) -> Dict[str, Any]:
        """Processes plain text, Markdown, or raw content."""
        cleaned = cls.clean_text(content)
        return {
            "text": cleaned,
            "metadata": {
                "title": title,
                "source_url": source_url or "",
                "content_hash": cls.calculate_hash(cleaned)
            }
        }

    @classmethod
    def load_file(cls, file_path: str) -> Dict[str, Any]:

        """Inspects file extension and extracts content."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return cls.load_pdf(file_path)
        elif ext in [".html", ".htm"]:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return cls.load_html(f.read(), source_url=file_path)
        else:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return cls.load_text(f.read(), title=os.path.basename(file_path), source_url=file_path)

document_loader = DocumentLoader()


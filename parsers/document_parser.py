import os
import re
from typing import Dict, List, Any

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import pypdfium2
except ImportError:
    pypdfium2 = None


class DocumentParser:
    """Extracts structured text and sections from PDF/TXT resumes or requisition files."""

    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extract raw text from PDF or TXT file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return DocumentParser._parse_pdf(file_path)
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

    @staticmethod
    def _clean_text(text: str) -> str:
        """Normalizes extracted text, fixing excessive single-word newlines and whitespace."""
        if not text:
            return ""
        # Fix vertical-text / word-per-line artifact (e.g. "WORD \n NEXT")
        text = re.sub(r'(\b\w+\b)\s*\n\s*(\b\w+\b)', r'\1 \2', text)
        # Normalize multiple spaces and multiple blank lines
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def extract_text_from_bytes(content: bytes, filename: str) -> str:
        """Extract text from in-memory file bytes (PDF or TXT)."""
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            # 1. Try pypdfium2 first for superior layout preservation
            if pypdfium2 is not None:
                try:
                    pdf = pypdfium2.PdfDocument(content)
                    text = ""
                    for page in pdf:
                        tp = page.get_textpage()
                        extracted = tp.get_text_range()
                        if extracted:
                            text += extracted + "\n"
                    if text.strip():
                        return text.strip()
                except Exception:
                    pass

            # 2. Try pypdf
            if pypdf is not None:
                import io
                try:
                    reader = pypdf.PdfReader(io.BytesIO(content))
                    text = ""
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
                    if text.strip():
                        return DocumentParser._clean_text(text)
                except Exception:
                    pass

            raw_ascii = re.sub(rb'[^\x20-\x7E\n\r\t]', b' ', content).decode('ascii', errors='ignore')
            return DocumentParser._clean_text(raw_ascii)
        else:
            return content.decode("utf-8", errors="ignore").strip()

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        # 1. Try pypdfium2 first
        if pypdfium2 is not None:
            try:
                pdf = pypdfium2.PdfDocument(file_path)
                text = ""
                for page in pdf:
                    tp = page.get_textpage()
                    extracted = tp.get_text_range()
                    if extracted:
                        text += extracted + "\n"
                if text.strip():
                    return text.strip()
            except Exception as e:
                print(f"[Warning] pypdfium2 failed: {e}. Trying fallback.")

        # 2. Try pypdf
        if pypdf is not None:
            try:
                reader = pypdf.PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                if text.strip():
                    return DocumentParser._clean_text(text)
            except Exception as e:
                print(f"[Warning] pypdf failed: {e}. Trying raw fallback.")

        # 3. Fallback reading
        with open(file_path, "rb") as f:
            content = f.read()
            raw_ascii = re.sub(rb'[^\x20-\x7E\n\r\t]', b' ', content).decode('ascii', errors='ignore')
        return DocumentParser._clean_text(raw_ascii)

    @staticmethod
    def extract_sections(text: str) -> Dict[str, str]:
        """Categorize resume text into functional sections: Experience, Projects, Skills, Education."""
        sections = {
            "summary": "",
            "experience": "",
            "projects": "",
            "skills": "",
            "education": "",
            "links": ""
        }

        lines = text.split("\n")
        current_section = "summary"
        
        # Regex headers
        header_patterns = {
            "experience": re.compile(r"^(work\s+)?experience|employment|work\s+history", re.IGNORECASE),
            "projects": re.compile(r"^projects|key\s+projects|open\s+source", re.IGNORECASE),
            "skills": re.compile(r"^skills|technical\s+skills|core\s+competencies", re.IGNORECASE),
            "education": re.compile(r"^education|academic\s+background|qualifications", re.IGNORECASE),
            "links": re.compile(r"^links|github|portfolio|websites", re.IGNORECASE),
        }

        for line in lines:
            clean_line = line.strip()
            if not clean_line:
                continue

            # Check header match
            matched_header = None
            for sec_name, pattern in header_patterns.items():
                if pattern.search(clean_line) and len(clean_line) < 40:
                    matched_header = sec_name
                    break

            if matched_header:
                current_section = matched_header
            else:
                sections[current_section] += clean_line + "\n"

        # Also extract raw URLs
        urls = re.findall(r'https?://[^\s]+|github\.com/[^\s]+', text)
        sections["links"] += "\n".join(urls)

        return sections

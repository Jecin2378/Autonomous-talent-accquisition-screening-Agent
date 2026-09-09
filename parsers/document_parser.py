import os
import re
from typing import Dict, List, Any

try:
    import pypdf
except ImportError:
    pypdf = None


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
    def extract_text_from_bytes(content: bytes, filename: str) -> str:
        """Extract text from in-memory file bytes (PDF or TXT)."""
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
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
                        return text
                except Exception:
                    pass
            return re.sub(rb'[^\x20-\x7E\n\r\t]', b' ', content).decode('ascii', errors='ignore')
        else:
            return content.decode("utf-8", errors="ignore")

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        text = ""
        if pypdf is not None:
            try:
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                return text
            except Exception as e:
                print(f"[Warning] pypdf failed: {e}. Falling back to text mode.")

        # Fallback reading
        with open(file_path, "rb") as f:
            content = f.read()
            # Basic ascii/utf-8 extraction fallback
            text = re.sub(rb'[^\x20-\x7E\n\r\t]', b' ', content).decode('ascii', errors='ignore')
        return text

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

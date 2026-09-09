from typing import Dict, List, Set


class SkillNormalizer:
    """Normalizes skill synonyms, abbreviations, and variant terminology."""

    SYNONYM_MAP: Dict[str, str] = {
        # Deep Learning & ML
        "torch": "PyTorch",
        "pytorch": "PyTorch",
        "tf": "TensorFlow",
        "tensorflow": "TensorFlow",
        "sklearn": "scikit-learn",
        "scikit-learn": "scikit-learn",
        "vllm": "vLLM",
        "deepspeed": "DeepSpeed",
        "ray": "Ray",
        "huggingface": "Hugging Face",
        "hf": "Hugging Face",

        # Cloud & Infra
        "k8s": "Kubernetes",
        "kubernetes": "Kubernetes",
        "docker": "Docker",
        "helm": "Helm",
        "aws": "AWS",
        "amazon web services": "AWS",
        "gcp": "Google Cloud",

        # Databases & Vector DB
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "pgvector": "Vector Database",
        "qdrant": "Vector Database",
        "milvus": "Vector Database",
        "chromadb": "Vector Database",
        "vector database": "Vector Database",

        # Languages
        "py": "Python",
        "python": "Python",
        "js": "JavaScript",
        "javascript": "JavaScript",
        "ts": "TypeScript",
        "typescript": "TypeScript",
        "golang": "Go",
        "go": "Go",
        "cpp": "C++",
        "c++": "C++",
        "rust": "Rust"
    }

    @classmethod
    def normalize(cls, skill_name: str) -> str:
        """Returns the canonical normalized skill name."""
        clean = skill_name.strip().lower()
        return cls.SYNONYM_MAP.get(clean, skill_name.strip().title())

    @classmethod
    def are_equivalent(cls, skill_a: str, skill_b: str) -> bool:
        """Returns True if skill_a and skill_b resolve to equivalent canonical skills."""
        norm_a = cls.normalize(skill_a).lower()
        norm_b = cls.normalize(skill_b).lower()

        if norm_a == norm_b:
            return True

        raw_a = skill_a.lower()
        raw_b = skill_b.lower()

        if norm_a in raw_b or norm_b in raw_a or raw_a in raw_b or raw_b in raw_a:
            return True

        # Check token intersection
        tokens_a = set(raw_a.replace('/', ' ').replace('-', ' ').split())
        tokens_b = set(raw_b.replace('/', ' ').replace('-', ' ').split())
        
        # Filter out common stop words
        stops = {"and", "or", "the", "in", "for", "with", "programming", "infrastructure", "deep", "learning"}
        t_a = tokens_a - stops
        t_b = tokens_b - stops

        if t_a and t_b and not t_a.isdisjoint(t_b):
            return True

        return False

    @classmethod
    def extract_canonical_skills(cls, text: str) -> List[str]:
        """Scans raw text and returns unique normalized skills present in text."""
        found: Set[str] = set()
        lowered = text.lower()
        for raw_term, canonical in cls.SYNONYM_MAP.items():
            if f" {raw_term} " in f" {lowered} " or f"({raw_term})" in lowered or f"/{raw_term}" in lowered or raw_term == lowered:
                found.add(canonical)
        return list(found)

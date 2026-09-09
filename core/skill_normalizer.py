from typing import Dict, List, Set, FrozenSet


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
        "azure": "Azure",
        "microsoft azure": "Azure",
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

    NON_EQUIVALENT_PAIRS: Set[FrozenSet[str]] = {
        frozenset({"docker", "kubernetes"}),
        frozenset({"docker", "k8s"}),
        frozenset({"aws", "azure"}),
        frozenset({"aws", "gcp"}),
        frozenset({"azure", "gcp"}),
        frozenset({"python", "rust"}),
        frozenset({"python", "c++"}),
    }

    @classmethod
    def normalize(cls, skill_name: str) -> str:
        """Returns the canonical normalized skill name."""
        clean = skill_name.strip().lower()
        return cls.SYNONYM_MAP.get(clean, skill_name.strip().title())

    @classmethod
    def are_equivalent(cls, skill_a: str, skill_b: str) -> bool:
        """Returns True if skill_a and skill_b resolve to equivalent canonical skills."""
        clean_a = skill_a.strip()
        clean_b = skill_b.strip()
        if not clean_a or not clean_b:
            return False

        norm_a = cls.normalize(clean_a).lower()
        norm_b = cls.normalize(clean_b).lower()

        pair = frozenset({norm_a, norm_b})
        if pair in cls.NON_EQUIVALENT_PAIRS:
            return False

        if norm_a == norm_b:
            return True

        raw_a = skill_a.lower()
        raw_b = skill_b.lower()

        if cls.normalize(raw_a) == cls.normalize(raw_b):
            return True

        # Check substring containment for complex titles (e.g. "PyTorch" inside "PyTorch / Deep Learning")
        if norm_a in norm_b or norm_b in norm_a or raw_a in raw_b or raw_b in raw_a:
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

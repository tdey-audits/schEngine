from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    faiss_index_path: str = "data/faiss.index"
    faiss_metadata_path: str = "data/metadata.json"
    pyq_faiss_index_path: str = "data/pyq_faiss.index"
    pyq_metadata_path: str = "data/pyq_metadata.json"
    exemplar_faiss_index_path: str = "data/exemplar_faiss.index"
    exemplar_metadata_path: str = "data/exemplar_metadata.json"
    science_faiss_index_path: str = "data/science_faiss.index"
    science_faiss_metadata_path: str = "data/science_metadata.json"
    science_pyq_faiss_index_path: str = "data/science_pyq_faiss.index"
    science_pyq_metadata_path: str = "data/science_pyq_metadata.json"
    science_exemplar_faiss_index_path: str = "data/science_exemplar_faiss.index"
    science_exemplar_metadata_path: str = "data/science_exemplar_metadata.json"

    llm_provider: str = "groq"
    llm_model: str = "llama-3.1-8b-instant"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 8192
    llm_request_timeout_seconds: float = 60.0
    llm_max_retries: int = 2
    llm_retry_backoff_seconds: float = 2.0

    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    huggingface_api_key: str = ""
    huggingface_base_url: str = "https://router.huggingface.co/v1"

    top_k_retrieved: int = 5
    rerank_top_k: int = 3
    min_chunk_length: int = 50
    max_chunk_length: int = 2000

    data_dir: str = "content/ncert/maths/ncert_maths_chapters"
    pyq_data_dir: str = "content/ncert/maths/math_cbse_pyqs"
    exemplar_data_dir: str = "content/ncert/maths/ncert_exemplar"
    science_data_dir: str = "content/ncert/science/ncert_science_chapter"
    science_pyq_data_dir: str = "content/ncert/science/pyqs"
    science_exemplar_data_dir: str = "content/ncert/science/ncert_exemplar_science"
    output_dir: str = "output"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def content_dir_for(self, subject: str, corpus: str = "textbook") -> str:
        subject = normalize_subject(subject)
        if subject == "science":
            return {
                "textbook": self.science_data_dir,
                "pyq": self.science_pyq_data_dir,
                "exemplar": self.science_exemplar_data_dir,
            }[corpus]
        return {
            "textbook": self.data_dir,
            "pyq": self.pyq_data_dir,
            "exemplar": self.exemplar_data_dir,
        }[corpus]

    def index_paths_for(self, subject: str, corpus: str = "textbook") -> tuple[str, str]:
        subject = normalize_subject(subject)
        if subject == "science":
            return {
                "textbook": (self.science_faiss_index_path, self.science_faiss_metadata_path),
                "pyq": (self.science_pyq_faiss_index_path, self.science_pyq_metadata_path),
                "exemplar": (self.science_exemplar_faiss_index_path, self.science_exemplar_metadata_path),
            }[corpus]
        return {
            "textbook": (self.faiss_index_path, self.faiss_metadata_path),
            "pyq": (self.pyq_faiss_index_path, self.pyq_metadata_path),
            "exemplar": (self.exemplar_faiss_index_path, self.exemplar_metadata_path),
        }[corpus]


def normalize_subject(subject: str | None) -> str:
    value = (subject or "maths").strip().lower()
    aliases = {
        "math": "maths",
        "mathematics": "maths",
        "maths": "maths",
        "science": "science",
        "sci": "science",
    }
    if value not in aliases:
        raise ValueError(f"Unsupported subject: {subject}")
    return aliases[value]


settings = Settings()

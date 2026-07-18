from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017/compliance_b2b"
    jwt_secret: str = "compliance_b2b_secret_2024"
    jwt_expire_days: int = 7
    port: int = 5000
    cors_origins: str = "http://localhost:5173"
    supabase_url: str | None = None
    supabase_anon_key: str | None = None

    # Google GenAI (Gemini/Gemma via AI Studio). Model tags are placeholders —
    # confirm actual availability with client.models.list() before relying on them.
    gemini_api_key: str | None = None
    gemini_vision_model: str = "gemma-4-26b-a4b-it"
    gemini_text_model: str = "gemma-4-26b-a4b-it"

    # Qdrant. Defaults to in-memory for local/hackathon use; set qdrant_url for a
    # real deployment (e.g. Qdrant Cloud or a self-hosted instance).
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None

    # Meta WhatsApp Cloud API
    whatsapp_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_verify_token: str | None = None
    whatsapp_api_version: str = "v20.0"
    # Optional: enables X-Hub-Signature-256 verification on the POST webhook
    # when set. Skipped (not enforced) if left unset, to keep local/hackathon
    # testing simple — set this in any deployment reachable from the internet.
    whatsapp_app_secret: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        # Any .env key without a matching field otherwise crashes startup
        # (bit us once already with stray Supabase keys) — safe to ignore
        # rather than hard-fail, since deploy hosts often carry extra env
        # vars beyond what this app declares.
        extra = "ignore"


settings = Settings()

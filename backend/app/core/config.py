"""Configuração central da aplicação, lida a partir de variáveis de ambiente (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict

JWT_SECRET_PADRAO = "dev-secret-troque-em-producao"

# Valores de exemplo que jamais podem ir para produção.
SEGREDOS_DE_EXEMPLO = {
    JWT_SECRET_PADRAO,
    "gere_uma_chave_secreta_longa_e_aleatoria",
    "troque_esta_senha",
    "troque-esta-chave",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "desenvolvimento" ou "producao". Em produção os segredos são obrigatórios.
    AMBIENTE: str = "desenvolvimento"

    # Banco
    DATABASE_URL: str = "postgresql+psycopg://taemdia:troque_esta_senha@db:5432/taemdia"

    # JWT
    JWT_SECRET: str = JWT_SECRET_PADRAO
    JWT_EXPIRE_MINUTES: int = 1440

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    # Endereço do frontend (destino do login e origem liberada no CORS)
    FRONTEND_URL: str = "http://localhost:4200"

    # Evolution API (WhatsApp)
    EVOLUTION_API_URL: str = ""
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCIA: str = "taemdia"

    # Segredo que autentica as chamadas ao webhook do WhatsApp.
    WEBHOOK_TOKEN: str = ""

    # Agendador de tarefas em segundo plano
    AGENDADOR_ATIVO: bool = True

    # --- Assinatura ---------------------------------------------------------
    # Administradores que conferem comprovantes. Fica em variável de ambiente,
    # e não em coluna do banco, para que ninguém vire administrador por
    # gravação: não existe bit a inverter.
    ADMIN_EMAILS: str = ""

    # Chave Pix mostrada em "Minha assinatura".
    PIX_CHAVE: str = ""
    PIX_NOME: str = ""
    ASSINATURA_VALOR: float = 19.90

    # Onde os comprovantes ficam guardados. Nunca é servido como pasta pública.
    UPLOADS_DIR: str = "/app/uploads"

    @property
    def em_producao(self) -> bool:
        return self.AMBIENTE.lower().startswith("prod")

    @property
    def administradores(self) -> list[str]:
        """E-mails com acesso à conferência de comprovantes, em minúsculas."""
        return [e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()]

    @property
    def origens_permitidas(self) -> list[str]:
        """Origens liberadas no CORS (separe por vírgula para aceitar mais de uma)."""
        return [origem.strip() for origem in self.FRONTEND_URL.split(",") if origem.strip()]

    def validar_para_producao(self) -> list[str]:
        """Lista os problemas de configuração que impedem subir em produção."""
        problemas = []
        if self.JWT_SECRET in SEGREDOS_DE_EXEMPLO or len(self.JWT_SECRET) < 32:
            problemas.append(
                "JWT_SECRET precisa ser uma chave própria com pelo menos 32 caracteres."
            )
        if "troque_esta_senha" in self.DATABASE_URL:
            problemas.append("A senha padrão do banco continua no DATABASE_URL.")
        if self.WEBHOOK_TOKEN in SEGREDOS_DE_EXEMPLO:
            problemas.append("WEBHOOK_TOKEN está com um valor de exemplo.")
        if not self.WEBHOOK_TOKEN:
            problemas.append(
                "WEBHOOK_TOKEN precisa ser definido para proteger o webhook do WhatsApp."
            )
        if not self.GOOGLE_CLIENT_ID or not self.GOOGLE_CLIENT_SECRET:
            problemas.append("As credenciais do Google OAuth não estão configuradas.")
        if any(o.startswith("http://") for o in self.origens_permitidas):
            problemas.append("FRONTEND_URL deve usar HTTPS em produção.")
        return problemas


settings = Settings()

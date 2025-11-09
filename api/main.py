"""
Brain RH API - Point d'entrée FastAPI
API REST pour matching CV/Offre avec LLM
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
from pathlib import Path
import logging
import os
from dotenv import load_dotenv

from api.routers import cvs, offres, matching, projects, enterprises, interview_sheet
from brainrh.paths import PROJECT_ROOT

# Charger les variables d'environnement depuis .env
load_dotenv(PROJECT_ROOT / ".env")

# Configuration du logging AVANT tout log
logs_dir = Path(__file__).parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'api_debug.log', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("🚀 Démarrage de l'API Brain RH")

# Vérification XAI_API_KEY (APRÈS la configuration du logging)
xai_key = os.environ.get('XAI_API_KEY')
if xai_key:
    logger.info(f"✅ XAI_API_KEY détectée → Grok sera utilisé pour le reranking")
else:
    logger.warning("⚠️ XAI_API_KEY non trouvée → Seul OpenAI sera disponible pour le reranking")

# Créer application FastAPI
app = FastAPI(
    title="Brain RH API",
    version="1.0.0",
    description="""
API de matching intelligent CV/Offre avec analyse LLM.

**Fonctionnalités:**
- Parsing de CVs (PDF/DOCX) avec extraction LLM
- Enrichissement d'offres avec génération must-have/nice-have
- Matching avec filtrage, scoring et re-ranking LLM
- Streaming temps-réel (SSE) pour traitements longs
- Gestion de projets et entreprises
- Génération de fiches d'entretien structurées
- Export CSV/JSON des résultats

**Documentation interactive:** `/docs` (Swagger UI) ou `/redoc` (ReDoc)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS pour développement local
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React (CRA)
        "http://localhost:5173",  # Vite
        "http://localhost:8501",  # Streamlit (pour coexistence)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(cvs.router, prefix="/api/v1/cvs", tags=["CVs"])
app.include_router(offres.router, prefix="/api/v1/offres", tags=["Offres"])
app.include_router(matching.router, prefix="/api/v1/matching", tags=["Matching"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projets"])
app.include_router(enterprises.router, prefix="/api/v1/enterprises", tags=["Entreprises"])
app.include_router(interview_sheet.router, prefix="/api/v1/interview-sheet", tags=["Fiches d'entretien"])


@app.get("/")
def root():
    """Page d'accueil de l'API"""
    return {
        "name": "Brain RH API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
def health():
    """Endpoint de santé pour monitoring"""
    return {"status": "ok"}


@app.get("/api/v1/files/{file_path:path}")
async def serve_file(file_path: str):
    """
    Sert les fichiers originaux (PDF/DOCX) depuis PROJECT_ROOT

    Args:
        file_path: Chemin relatif au PROJECT_ROOT

    Returns:
        FileResponse avec le fichier demandé

    Raises:
        HTTPException 404 si le fichier n'existe pas
        HTTPException 403 si le fichier est en dehors de PROJECT_ROOT
    """
    # Construire le chemin absolu
    absolute_path = (PROJECT_ROOT / file_path).resolve()

    # Vérifier que le fichier est bien sous PROJECT_ROOT (sécurité)
    try:
        absolute_path.relative_to(PROJECT_ROOT)
    except ValueError:
        raise HTTPException(status_code=403, detail="Accès refusé")

    # Vérifier que le fichier existe
    if not absolute_path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    # Vérifier que c'est bien un fichier (pas un dossier)
    if not absolute_path.is_file():
        raise HTTPException(status_code=400, detail="Chemin invalide")

    # Déterminer le content-type selon l'extension
    import mimetypes
    content_type = mimetypes.guess_type(str(absolute_path))[0] or "application/octet-stream"

    # Servir le fichier avec le bon content-type
    response = FileResponse(
        path=str(absolute_path),
        filename=absolute_path.name,
        media_type=content_type
    )
    # Force inline display pour PDFs (affichage navigateur au lieu de téléchargement)
    response.headers["Content-Disposition"] = f'inline; filename="{absolute_path.name}"'
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global des exceptions non gérées"""
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Erreur interne du serveur",
            "details": {"error": str(exc)}
        }
    )


if __name__ == "__main__":
    # Lancer le serveur en développement
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en développement
        log_level="info"
    )

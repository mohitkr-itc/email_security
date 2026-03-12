"""
Base FastAPI application for the Agentic Email Security System.

Exposes health check and email analysis endpoints.
This service will be extended in later phases with full agent orchestration.
"""

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from api.schemas import (
    EmailAnalysisRequest,
    EmailAnalysisResponse,
    HealthResponse,
)
from configs.settings import settings
from services.logging_service import setup_logging


# ---------------------------------------------------------------------------
# Application lifespan (startup / shutdown)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and clean up on shutdown."""
    # --- Startup ---
    setup_logging(
        log_dir=settings.log_dir,
        log_level=settings.app_log_level,
        log_format=settings.log_format,
    )
    logger.info(
        "Agentic Email Security API starting",
        environment=settings.app_env,
        host=settings.api_host,
        port=settings.api_port,
    )
    yield
    # --- Shutdown ---
    logger.info("Agentic Email Security API shutting down")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Agentic Email Security System",
    description=(
        "Production-grade Agentic AI system for phishing email detection. "
        "Uses multiple independent AI agents to analyze email components "
        "and collectively determine threat levels."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Return the current health status of the API service."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.app_env,
    )


@app.post(
    "/analyze-email",
    response_model=EmailAnalysisResponse,
    tags=["Analysis"],
)
async def analyze_email(request: EmailAnalysisRequest):
    """
    Accept an email for phishing analysis.

    In later phases this endpoint will dispatch email data to all analysis
    agents in parallel and return aggregated threat scores.

    Currently returns an acknowledgement placeholder.
    """
    analysis_id = str(uuid.uuid4())

    logger.info(
        "Email received for analysis",
        analysis_id=analysis_id,
        sender=request.headers.sender,
        subject=request.headers.subject,
        url_count=len(request.urls),
        attachment_count=len(request.attachments),
    )

    return EmailAnalysisResponse(
        status="received",
        message="Email received for analysis",
        analysis_id=analysis_id,
        agent_results=[],
        overall_risk_score=None,
    )

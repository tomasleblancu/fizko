"""
FastAPI application for SII integration service.
Simplified version without database or authentication.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sii, verify, celery
from app.routers.chat import agent as chat_agent
from app.routers.chat import chatkit as chat_chatkit
from app.routers.chat import conversations as chat_conversations

app = FastAPI(
    title="SII Integration Service",
    description="Simplified service for Chilean tax authority (SII) integration",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sii.router, prefix="/api/sii", tags=["SII"])
app.include_router(verify.router, prefix="/api/sii", tags=["SII Verification"])
app.include_router(celery.router, prefix="/api")  # Celery router includes its own prefix and tags
app.include_router(chat_agent.router, prefix="/api", tags=["Chat Agent"])
app.include_router(chat_chatkit.router, prefix="/api", tags=["ChatKit"])
app.include_router(chat_chatkit.router, tags=["ChatKit (root)"])  # Also register at root for backward compatibility
app.include_router(chat_conversations.router, prefix="/api", tags=["Conversations"])

@app.get("/")
async def root():
    return {
        "service": "SII Integration Service",
        "version": "2.0.0",
        "status": "running",
        "features": {
            "sii_integration": True,
            "chat_agents": True,
            "chatkit": True,
            "conversations": True,
            "celery_tasks": True,
            "database": False,
            "authentication": False
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

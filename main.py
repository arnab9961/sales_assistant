import os
import uvicorn
from app.main import app
from app.config import settings

if __name__ == "__main__":
    port = int(os.getenv("PORT", settings.PORT))
    host = os.getenv("HOST", settings.HOST)
    uvicorn.run("main:app", host=host, port=port, reload=settings.DEBUG)

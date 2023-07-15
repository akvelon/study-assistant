"""Study Assistant app entry point"""
import uvicorn

from settings import settings

if __name__ == "__main__":
    uvicorn.run('api.main:app', host="0.0.0.0", port=settings.port, root_path=settings.root_path)

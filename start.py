import uvicorn

from dotenv import load_dotenv

from settings import settings

if __name__ == "__main__":
    uvicorn.run('api.main:app', host="0.0.0.0", port=settings.port, root_path=settings.root_path)

"""FastAPI application with GigaChat API integration."""

from fastapi import FastAPI

from routes.router import router


app = FastAPI()
app.include_router(router)


import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
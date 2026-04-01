from fastapi import FastAPI

app = FastAPI(title="Sprite Atlas Builder API")


@app.get("/")
async def root():
    return {"message": "Sprite Atlas Builder API"}


@app.get("/health")
async def health():
    return {"status": "ok"}

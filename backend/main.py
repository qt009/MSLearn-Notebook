from fastapi import FastAPI
from app.scraper.routes import router as ScraperRouter
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(ScraperRouter)



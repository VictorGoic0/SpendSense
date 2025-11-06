from fastapi import FastAPI

app = FastAPI(title="SpendSense API", version="1.0.0")


@app.get("/")
async def root():
    return {"message": "SpendSense API"}


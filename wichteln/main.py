from fastapi import FastAPI
from wichteln.routes import router
from wichteln.database import init_db

app = FastAPI(title="Wichteln - Secret Santa Exchange")

@app.on_event("startup")
async def startup():
    await init_db()

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("wichteln.main:app", host="0.0.0.0", port=8000, reload=True)
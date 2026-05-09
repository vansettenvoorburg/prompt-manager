import os
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


class PromptRequest(BaseModel):
    rol: str
    taak: str
    doel: str
    formaat: str = ""
    stijl: str = ""
    scope: str = ""
    eisen: str = ""
    voorbeelden: str = ""


def bouw_prompt(body: PromptRequest) -> str:
    regels = [f"Als {body.rol} wil ik {body.taak} zodat {body.doel}."]
    if body.formaat:
        regels.append(f"Formaat: {body.formaat}")
    if body.stijl:
        regels.append(f"Stijl: {body.stijl}")
    if body.scope:
        regels.append(f"Scope: {body.scope}")
    if body.eisen:
        regels.append(f"Extra eisen: {body.eisen}")
    if body.voorbeelden:
        regels.append(f"Voorbeelden: {body.voorbeelden}")
    return "\n".join(regels)


async def call_ollama(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json()["response"]
        except httpx.HTTPError as exc:
            raise ConnectionError("Ollama niet bereikbaar") from exc


@app.post("/api/prompt")
async def handle_prompt(body: PromptRequest):
    ontbrekend = [v for v in ("rol", "taak", "doel") if not getattr(body, v).strip()]
    if ontbrekend:
        raise HTTPException(
            status_code=400,
            detail=f"Verplicht veld ontbreekt: {', '.join(ontbrekend)}",
        )
    prompt = bouw_prompt(body)
    try:
        result = await call_ollama(prompt)
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"response": result}


app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)

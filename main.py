
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent

# Conta do TikTok que fará a live
USUARIO_TIKTOK = "@isabelaaaoiii"

# Contadores de comentários
votos = {"13": 0, "22": 0}
status = "Aguardando conexão"

client = TikTokLiveClient(unique_id=USUARIO_TIKTOK)


@client.on(CommentEvent)
async def receber_comentario(event: CommentEvent):
    texto = event.comment.strip()

    if texto == "13" or texto == "22":
        votos[texto] += 1
        print(f"Comentário {texto} recebido! Total: {votos}")


async def conectar_tiktok():
    global status

    while True:
        try:
            status = "Conectando ao TikTok"
            print("Tentando conectar à live...")
            await client.start()
            status = "Conexão encerrada"
        except asyncio.CancelledError:
            raise
        except Exception as erro:
            status = "Aguardando live ou reconexão"
            print("Erro na conexão:", erro)

        await asyncio.sleep(15)


@asynccontextmanager
async def lifespan(app: FastAPI):
    tarefa = asyncio.create_task(conectar_tiktok())
    try:
        yield
    finally:
        tarefa.cancel()
        try:
            await tarefa
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://luanbarbosa12278-max.github.io"
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
async def inicio():
    return {"mensagem": "Servidor de votação funcionando!"}


@app.get("/votos")
async def consultar_votos():
    total = votos["13"] + votos["22"]

    return {
        "13": votos["13"],
        "22": votos["22"],
        "total": total,
        "porcentagem_13": round(votos["13"] / total * 100, 1) if total else 0,
        "porcentagem_22": round(votos["22"] / total * 100, 1) if total else 0,
        "status": status,
    }
    


import asyncio
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent


# CONFIGURAÇÕES
USUARIO_INICIAL = "@isabelaaaoiii"
SENHA_ADMIN = os.environ.get("ADMIN_PASSWORD", "")

ORIGEM_SITE = "https://luanbarbosa12278-max.github.io"

# ESTADO DO SERVIDOR
votos = {"13": 0, "22": 0}
usuario_atual = USUARIO_INICIAL
status = "Aguardando conexão"

tarefa_tiktok = None
geracao = 0


class TrocarUsuario(BaseModel):
    usuario: str


def validar_senha(senha):
    if not SENHA_ADMIN:
        raise HTTPException(
            status_code=503,
            detail="Configure ADMIN_PASSWORD no Render."
        )

    if not secrets.compare_digest(
        senha or "",
        SENHA_ADMIN
    ):
        raise HTTPException(
            status_code=401,
            detail="Senha de administrador incorreta."
        )


def normalizar_usuario(usuario):
    usuario = usuario.strip().lstrip("@")

    if not usuario:
        raise HTTPException(
            status_code=400,
            detail="Digite um usuário do TikTok."
        )

    if len(usuario) > 24 or not all(
        c.isalnum() or c in "._"
        for c in usuario
    ):
        raise HTTPException(
            status_code=400,
            detail="Usuário do TikTok inválido."
        )

    return "@" + usuario


async def acompanhar_live(usuario, minha_geracao):
    global status

    client = TikTokLiveClient(unique_id=usuario)

    @client.on(CommentEvent)
    async def receber_comentario(event: CommentEvent):
        if minha_geracao != geracao:
            return

        texto = event.comment.strip()

        if texto in votos:
            votos[texto] += 1

            print(
                f"{usuario}: comentário {texto}, "
                f"total {votos}",
                flush=True
            )

    try:
        while minha_geracao == geracao:
            try:
                status = "Conectando à LIVE"

                print(
                    f"Tentando conectar a {usuario}",
                    flush=True
                )

                await client.start()

                if minha_geracao == geracao:
                    status = "Conexão encerrada"

            except asyncio.CancelledError:
                raise

            except Exception as erro:
                if minha_geracao == geracao:
                    status = "Aguardando live ou reconexão"

                print(
                    f"Erro de conexão: {erro}",
                    flush=True
                )

            await asyncio.sleep(15)

    except asyncio.CancelledError:
        print(
            f"Conexão de {usuario} cancelada.",
            flush=True
        )
        raise

    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def iniciar_conexao(usuario):
    global tarefa_tiktok, usuario_atual
    global status, geracao

    usuario = normalizar_usuario(usuario)

    # Cancela a conexão anterior
    geracao += 1

    if tarefa_tiktok is not None:
        tarefa_tiktok.cancel()

        try:
            await asyncio.wait_for(
                tarefa_tiktok,
                timeout=5
            )
        except (
            asyncio.CancelledError,
            asyncio.TimeoutError
        ):
            pass

    usuario_atual = usuario
    status = "Conectando à LIVE"

    # Zera os comentários ao trocar de conta
    votos["13"] = 0
    votos["22"] = 0

    tarefa_tiktok = asyncio.create_task(
        acompanhar_live(usuario, geracao)
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await iniciar_conexao(USUARIO_INICIAL)

    try:
        yield
    finally:
        if tarefa_tiktok is not None:
            tarefa_tiktok.cancel()

            try:
                await tarefa_tiktok
            except asyncio.CancelledError:
                pass


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ORIGEM_SITE],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Admin-Password"],
)


@app.get("/")
async def inicio():
    return {
        "mensagem": "Servidor de votação funcionando!",
        "usuario": usuario_atual
    }


@app.get("/votos")
async def consultar_votos():
    total = votos["13"] + votos["22"]

    return {
        "13": votos["13"],
        "22": votos["22"],
        "total": total,
        "porcentagem_13": round(
            votos["13"] / total * 100, 1
        ) if total else 0,
        "porcentagem_22": round(
            votos["22"] / total * 100, 1
        ) if total else 0,
        "usuario": usuario_atual,
        "status": status
    }


@app.post("/configurar")
async def configurar(
    dados: TrocarUsuario,
    x_admin_password: str = Header(default="")
):
    validar_senha(x_admin_password)

    novo_usuario = normalizar_usuario(dados.usuario)

    await iniciar_conexao(novo_usuario)

    return {
        "sucesso": True,
        "usuario": usuario_atual,
        "mensagem": "Tentando conectar à nova LIVE."
    }
    

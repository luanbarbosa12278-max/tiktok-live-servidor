
import asyncio
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent

# Perfil que fará a live
client = TikTokLiveClient(unique_id="@isabelaaaoiii")

# Contadores
votos = {
    "13": 0,
    "22": 0
}

@client.on(CommentEvent)
async def receber_comentario(event: CommentEvent):
    texto = event.comment.strip()

    # Só aceita 13 ou 22
    if texto not in votos:
        return

    # Cada comentário válido conta como um voto
    # A mesma pessoa pode votar várias vezes
    votos[texto] += 1

    total = votos["13"] + votos["22"]

    porcentagem_13 = (
        votos["13"] / total * 100 if total else 0
    )

    porcentagem_22 = (
        votos["22"] / total * 100 if total else 0
    )

    print("--------------------------")
    print("Novo comentário:", texto)
    print("Usuário:", event.user.unique_id)
    print("Votos 13:", votos["13"])
    print("Votos 22:", votos["22"])
    print("Total:", total)
    print(f"13: {porcentagem_13:.1f}%")
    print(f"22: {porcentagem_22:.1f}%")
    print("--------------------------")

async def main():
    print("Conectando ao TikTok LIVE...")
    await client.start()

if __name__ == "__main__":
    asyncio.run(main())

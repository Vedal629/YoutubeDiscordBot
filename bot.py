import discord
from discord.ext import commands
from music import Music

import config  # 토큰, 프리픽스 설정 파일

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"봇 작동 중: {bot.user}")

async def main():
    async with bot:
        await bot.add_cog(Music(bot))
        await bot.start(config.DISCORD_TOKEN)

import asyncio
asyncio.run(main())

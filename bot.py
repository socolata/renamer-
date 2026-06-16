import discord
import os
from dotenv import load_dotenv
from syntax_fixer import advanced_lua_processor, is_obfuscated
load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
@client.event
async def on_ready():
    print(f"Logged in as {client.user.name}")
    print("Bot is up and ready")
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    content = message.content.strip()
    if content.startswith("!purge chat"):
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send("You do not have permission to use this command.")
            return
        parts = content.split()
        if len(parts) < 3:
            await message.channel.send("Please specify the amount. Example: `!purge chat 10`")
            return
        try:
            amount = int(parts[2])
            deleted = await message.channel.purge(limit=amount + 1)
            confirm_msg = await message.channel.send(f"Successfully purged {len(deleted) - 1} messages.")
            await confirm_msg.delete(delay=3)
        except Exception:
            await message.channel.send("An error occurred during purge.")
        return
    if not (content.startswith(".rename") or content.startswith("!rename")):
        return
    raw_lua_code = ""
    if message.attachments:
        attachment = message.attachments[0]
        try:
            file_bytes = await attachment.read()
            raw_lua_code = file_bytes.decode('utf-8', errors='ignore')
        except Exception:
            await message.channel.send("Error reading uploaded file.")
            return
    else:
        code_segment = content[7:].strip()
        if code_segment.startswith("```"):
            lines = code_segment.splitlines()
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_lua_code = "\n".join(lines)
        else:
            raw_lua_code = code_segment
    if not raw_lua_code.strip():
        await message.channel.send("Please provide script code.")
        return
    if is_obfuscated(raw_lua_code):
        await message.channel.send("Process denied. Script is obfuscated.")
        return
    status_msg = await message.channel.send("Processing script, please wait...")
    try:
        final_output = advanced_lua_processor(raw_lua_code)
        temp_file_path = f"processed_{message.id}.lua"
        with open(temp_file_path, "w", encoding="utf-8") as file:
            file.write(final_output)
        await message.channel.send(content="Here is your clean script.", file=discord.File(temp_file_path, filename="cleaned_script.lua"))
    except Exception as e:
        await message.channel.send(f"An error occurred while processing: {str(e)}")
    finally:
        try:
            await status_msg.delete()
        except:
            pass
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if BOT_TOKEN:
    client.run(BOT_TOKEN)
else:
    print("CRITICAL ERROR: BOT_TOKEN not found in .env file!")
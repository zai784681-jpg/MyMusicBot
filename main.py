main.py
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from youtube_search_python import VideosSearch
import yt_dlp

# --- CONFIGURATION (FILL YOUR DETAILS HERE) ---
API_ID = 33640539
API_HASH = "17b88aa765b3f20d75394a81c3b17646" # Replace with your API Hash
BOT_TOKEN = "8222947184:AAHLfmDtW7YnINLdrRfqwOIjkMUx7Smtux8" # Replace with Bot Token
SESSION_STRING = "QIBUFsAxxYaaDLVstEyagPidAn8CqEeA7EAY75Hg4kJj9lNMZ-Jb_3sIjKLYeTfXAMdnokUQTZ73IW5LMvJ5xFch695TdwOBTXoux--ECQYakoN1kDNnYAPObebHtx5rQZA-Yt6_xmqHBM-B6ro0a0r_p-d8NQ52VxNWy0X5q2ZLf9r7mDe-vs68pMpTVfql1vjmMvWJaXnDvmVtURlCUJDZFII068TQWZTnCxlta4u1IhqQKel1OYYzloRkGFIXPmfNcU2cvi_0IVCMA2OtJW-kOs9VGR2e8CJqzbooqiIlPEys3yrz9bUF5xq393LUrNy1VI5KmR2IZrvwaONsjCXcEDluAAAAAGX3N7BAA" # Paste the code from Step 2

app = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_app = Client("MusicAssistant", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(user_app)

search_db = {}

def get_buttons(results, page=0):
    buttons = []
    start = page * 5
    end = start + 5
    current_results = results[start:end]

    for video in current_results:
        buttons.append([
            InlineKeyboardButton(
                text=f"{video['title'][:30]}...", 
                callback_data=f"play|{video['id']}"
            )
        ])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"page|{page-1}"))
    if end < len(results):
        nav_buttons.append(InlineKeyboardButton("More ➡️", callback_data=f"page|{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
        
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Bot Started! Search any song by name.")

@app.on_message(filters.text & ~filters.private)
async def search_music(client, message):
    query = message.text
    if query.startswith("/"): return
    
    m = await message.reply_text(f"🔎 Searching: {query}...")
    search = VideosSearch(query, limit=20) # Fetches 20 results
    results = search.result()['result']
    
    if not results:
        await m.edit("No song found.")
        return

    search_db[message.chat.id] = results
    await m.edit(
        f"🎵 **Results for:** {query}",
        reply_markup=get_buttons(results, page=0)
    )

@app.on_callback_query()
async def handle_query(client, callback: CallbackQuery):
    data = callback.data.split("|")
    action = data[0]
    
    if action == "page":
        page = int(data[1])
        results = search_db.get(callback.message.chat.id)
        if results:
            await callback.message.edit_reply_markup(reply_markup=get_buttons(results, page))
            
    elif action == "play":
        video_id = data[1]
        link = f"https://www.youtube.com/watch?v={video_id}"
        chat_id = callback.message.chat.id
        
        await callback.answer("Processing...", show_alert=False)
        await callback.message.edit(f"📥 **Downloading...**")
        
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "-g", "-f", "bestaudio", link,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        stream_link = stdout.decode().strip()

        try:
            await call_py.play(chat_id, MediaStream(stream_link))
            await callback.message.edit(f"▶️ **Playing:** {link}")
        except Exception as e:
            await callback.message.edit(f"Error: {e}")

async def main():
    await app.start()
    await user_app.start()
    await call_py.start()
    print("Bot Deployed Successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

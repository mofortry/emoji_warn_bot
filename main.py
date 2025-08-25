import os
import json
import regex as re
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from dotenv import load_dotenv
from datetime import timedelta

# تحميل إعدادات البيئة
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client(
    "emoji_warn_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

WARNINGS_FILE = "warnings.json"

# تحميل التحذيرات من الملف
if os.path.exists(WARNINGS_FILE):
    with open(WARNINGS_FILE, "r", encoding="utf-8") as f:
        warnings = json.load(f)
else:
    warnings = {}

# حفظ التحذيرات
def save_warnings():
    with open(WARNINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(warnings, f, ensure_ascii=False, indent=2)

# دالة للتحقق من وجود إيموجي
def contains_emoji(text: str) -> bool:
    if not text:
        return False
    emoji_pattern = re.compile(r"\p{Emoji}", re.UNICODE)
    return bool(emoji_pattern.search(text))

# متابعة الرسائل في الجروب
@app.on_message((filters.text | filters.caption) & filters.group)
async def check_emoji(client, message):
    text_to_check = message.text or message.caption or ""
    if contains_emoji(text_to_check):
        user_id = str(message.from_user.id)
        user_name = message.from_user.mention

        # زيادة التحذير
        warnings[user_id] = warnings.get(user_id, 0) + 1
        warn_count = warnings[user_id]
        save_warnings()

        # الرد على العضو
        await message.reply_text(f"⚠️ {user_name} عندك {warn_count} تحذير(ات).", quote=True)

        # لو وصل لآخر تحذير (3)
        if warn_count >= 3:
            mute_duration = timedelta(days=2)  # الميوت لمدة يومين
            await app.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=int(user_id),
                permissions=ChatPermissions(can_send_messages=False),
                until_date=message.date + mute_duration
            )
            await message.reply_text(f"🚫 {user_name} تم ميوت لمدة يومين بسبب 3 تحذيرات!", quote=True)
            # إعادة التحذيرات للصفر بعد الميوت
            warnings[user_id] = 0
            save_warnings()

# أمر /warnings لعرض التحذيرات
@app.on_message(filters.command("warnings") & filters.group)
async def get_warnings(client, message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        user = await app.get_users(message.command[1])
    else:
        return await message.reply_text("ℹ️ استخدم الرد على رسالة أو /warnings @username")

    user_id = str(user.id)
    warn_count = warnings.get(user_id, 0)
    await message.reply_text(f"👤 {user.mention} عنده {warn_count} تحذير(ات).")

# أمر /resetwarns لمسح التحذيرات
@app.on_message(filters.command("resetwarns") & filters.group)
async def reset_warnings(client, message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        user = await app.get_users(message.command[1])
    else:
        return await message.reply_text("ℹ️ استخدم الرد على رسالة أو /resetwarns @username")

    user_id = str(user.id)
    warnings[user_id] = 0
    save_warnings()
    await message.reply_text(f"✅ تم مسح التحذيرات عن {user.mention}.")

print("🚀 البوت شغال...")
app.run()

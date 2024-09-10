import os
import logging
import random
import asyncio
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from database.users_chats_db import db
from info import *
from utils import get_settings, get_size, is_subscribed, save_group_settings, temp
from database.connections_mdb import active_connection
import pytz
import datetime
from utils import get_seconds, get_tutorial, get_shortlink
from database.users_chats_db import db 
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong
import re
import json
import base64
logger = logging.getLogger(__name__)

BATCH_FILES = {}

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [
            [
                InlineKeyboardButton('🔍 Group​​​​​', url=f'https://t.me/{MOVIE_GROUP_USERNAME}')
            ],
            [
                InlineKeyboardButton('🙆🏻 Hᴇʟᴘ 🦾', url=f"https://t.me/{temp.U_NAME}?start=help"),
            ],[
            InlineKeyboardButton('⪦ 𝕄𝕆𝕍𝕀𝔼 ℂℍ𝔸ℕℕ𝔼𝕃 ⪧', url='https://t.me/real_MoviesAdda3')
            ],[
            InlineKeyboardButton('💸 E𝐚𝐫𝐧 M𝐨𝐧𝐞𝐲 💸', callback_data="shortlink_info")
            ],
            [
                InlineKeyboardButton(text=DOWNLOAD_TEXT_NAME,url=DOWNLOAD_TEXT_URL)
            ]
            ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(script.START_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME), reply_markup=reply_markup)
        await asyncio.sleep(2) # 😢 https://github.com/LazyDeveloperr/LazyPrincess/blob/master/plugins/p_ttishow.py#L17 😬 wait a bit, before checking.
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
        return 
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('↖️ Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘs ↗️', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('🧞‍♀️ Sᴇᴀʀᴄʜ', switch_inline_query_current_chat=''),
            InlineKeyboardButton('🔍 Gʀᴏᴜᴘ', url=f'https://t.me/{MOVIE_GROUP_USERNAME}')
            ],[
            InlineKeyboardButton('🙆🏻 Hᴇʟᴘ ', callback_data='help'),
            InlineKeyboardButton('🎁 Hᴇʟᴘ++', callback_data='leech_url_help'),
            ],[
            InlineKeyboardButton('⚙ Sᴇᴛᴛɪɴɢs', callback_data='openSettings'),
            InlineKeyboardButton('♥️ Aʙᴏᴜᴛ', callback_data='about')
            ],[
            InlineKeyboardButton('⪦ 𝕄𝕆𝕍𝕀𝔼 ℂℍ𝔸ℕℕ𝔼𝕃 ⪧', url='https://t.me/real_MoviesAdda3')
            ],[
            InlineKeyboardButton('💸 E𝐚𝐫𝐧 M𝐨𝐧𝐞𝐲 💸', callback_data="shortlink_info")
            ],[
                InlineKeyboardButton(
                    "🦋 SUBSCRIBE YT Channel 🦋", url='https://youtube.com/@LazyDeveloperr'
                )
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL), creates_join_request=True)
        except ChatAdminRequired:
            logger.error("Hey Sona, Ek dfa check kr lo ki main Channel mei Add hu ya nhi...!")
            return
        btn = [
            [
                InlineKeyboardButton(
                    "🤖 Join Updates Channel", url=invite_link.invite_link
                )
            ],
             [
                InlineKeyboardButton(
                    "🦋 SUBSCRIBE YT Channel 🦋", url='https://youtube.com/@LazyDeveloperr'
                )
            ]
        ]

        if message.command[1] != "subscribe":
            try:
                kk, file_id = message.command[1].split("_", 1)
                pre = 'checksubp' if kk == 'filep' else 'checksub' 
                btn.append([InlineKeyboardButton(" 🔄 Try Again", callback_data=f"{pre}#{file_id}")])
            except (IndexError, ValueError):
                btn.append([InlineKeyboardButton(" 🔄 Try Again", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
        await client.send_message(
            chat_id=message.from_user.id,
            text="**Please Join My Updates Channel to use this Bot!**",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.MARKDOWN
            )
        return
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [[
            InlineKeyboardButton('↖️ Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘs ↗️', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('🧞‍♀️ Sᴇᴀʀᴄʜ', switch_inline_query_current_chat=''),
            InlineKeyboardButton('🔍 Gʀᴏᴜᴘ', url=f'https://t.me/{MOVIE_GROUP_USERNAME}')
            ],[
            InlineKeyboardButton('🙆🏻 Hᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('🎁 Hᴇʟᴘ++ ', callback_data='leech_url_help'),
        ],[
            InlineKeyboardButton('⚙ Sᴇᴛᴛɪɴɢs', callback_data='openSettings'),
            InlineKeyboardButton('♥️ Aʙᴏᴜᴛ', callback_data='about')
            ],
        [
            InlineKeyboardButton('⪦ 𝕄𝕆𝕍𝕀𝔼 ℂℍ𝔸ℕℕ𝔼𝕃 ⪧', url='https://t.me/real_MoviesAdda3')
        ],
        [
            InlineKeyboardButton('💸 E𝐚𝐫𝐧 M𝐨𝐧𝐞𝐲 💸', callback_data="shortlink_info")
        ],[
                InlineKeyboardButton(
                    "🦋 SUBSCRIBE YT Channel 🦋", url='https://youtube.com/@LazyDeveloperr'
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    if data.split("-", 1)[0] == "BATCH":
        sts = await message.reply("Please wait")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs
        for msg in msgs:
            title = msg.get("title")
            size=get_size(int(msg.get("size", 0)))
            f_caption=msg.get("caption", "")
            if BATCH_FILE_CAPTION:
                try:
                    f_caption=BATCH_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{title}"
            try:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    )
            except FloodWait as e:
                await asyncio.sleep(e.x)
                logger.warning(f"Floodwait of {e.x} sec.")
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton('▶ Gen Stream / Download Link', callback_data=f'generate_stream_link:{file_id}'),
                            ],
                            [
                                InlineKeyboardButton('📌 ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 📌', url=f'https://t.me/LazyDeveloperr')
                            ]
                        ]
                    )
                    )
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
            await asyncio.sleep(1) 
        await sts.delete()
        return
    elif data.split("-", 1)[0] == "DSTORE":
        sts = await message.reply("Please wait")
        b_string = data.split("-", 1)[1]
        decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
        try:
            f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
        except:
            f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
            protect = "/pbatch" if PROTECT_CONTENT else "batch"
        diff = int(l_msg_id) - int(f_msg_id)
        async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
            if msg.media:
                media = getattr(msg, msg.media.value)
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption=BATCH_FILE_CAPTION.format(file_name=getattr(media, 'file_name', ''), file_size=getattr(media, 'file_size', ''), file_caption=getattr(msg, 'caption', ''))
                    except Exception as e:
                        logger.exception(e)
                        f_caption = getattr(msg, 'caption', '')
                else:
                    media = getattr(msg, msg.media.value)
                    file_name = getattr(media, 'file_name', '')
                    f_caption = getattr(msg, 'caption', file_name)
                try:
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            elif msg.empty:
                continue
            else:
                try:
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            await asyncio.sleep(1) 
        return await sts.delete()
    
    if data.startswith("sendfiles"):
        try:
            userid = message.from_user.id if message.from_user else None
            chat_id = int("-" + file_id.split("-")[1])

            ghost_url = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=allfiles_{file_id}")

            client_msg = await client.send_message(
                chat_id=userid,
                text=f"👋 Hey {message.from_user.mention}\n\nDownload Link Generated ✔, Kindly click on download button below 👇 .\n\n",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton('📁 ᴅᴏᴡɴʟᴏᴀᴅ 📁', url=ghost_url)
                        ],
                        [
                            InlineKeyboardButton('🎉 ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ : ʀᴇᴍᴏᴠᴇ ᴀᴅꜱ 🎊', callback_data="seeplans")
                        ]
                    ]
                )
            )

            await asyncio.sleep(1800)
            await client_msg.edit("<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ !\nᴋɪɴᴅʟʏ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>")
            return
        except Exception as e:
            print(f"Error handling sendfiles: {e}")

    elif data.startswith("short"):         
        user_id = message.from_user.id
        chat_id = temp.SHORT.get(user_id)
        files_ = await get_file_details(file_id)
        files = files_[0]
        ghost = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")
        k = await client.send_message(
            chat_id=user_id,
            text=f"🫂 ʜᴇʏ {message.from_user.mention}\n\n✅ ʏᴏᴜʀ ʟɪɴᴋ ɪꜱ ʀᴇᴀᴅʏ, ᴋɪɴᴅʟʏ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴜᴛᴛᴏɴ.\n\n🎁 ꜰɪʟᴇ ɴᴀᴍᴇ : <code>{files.file_name}</code> \n\n⚕ ꜰɪʟᴇ ꜱɪᴢᴇ : <code>{get_size(files.file_size)}</code>\n\n",
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton('📁 ᴅᴏᴡɴʟᴏᴀᴅ 📁', url=ghost)
                ],[
                    InlineKeyboardButton('✨ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ : ʀᴇᴍᴏᴠᴇ ᴀᴅꜱ ✨', callback_data="seeplans")
                ]]
            )
        )
        await asyncio.sleep(600)
        await k.edit("<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ !\nᴋɪɴᴅʟʏ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>")
        return
    
    elif data.startswith("all"):
        # print('Help lazy bhai ! i am hit')
        files = temp.GETALL.get(file_id)
        if not files:
            return await message.reply('<b><i>ɴᴏ ꜱᴜᴄʜ ꜰɪʟᴇ ᴇxɪꜱᴛꜱ !</b></i>')
        filesarr = []
        for file in files:
            file_id = file.file_id
            files_ = await get_file_details(file_id)
            files1 = files_[0]
            title = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files1.file_name.split()))
            size=get_size(files1.file_size)
            f_caption=files1.caption
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files1.file_name.split()))}"
            
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                caption=f_caption,
                protect_content=True if pre == 'filep' else False,
                reply_markup=InlineKeyboardMarkup(
            [
             [
              InlineKeyboardButton('▶ Gen Stream / Download Link', callback_data=f'generate_stream_link:{file_id}'),
             ]
            ]
        )
    )
            filesarr.append(msg)
        k = await client.send_message(chat_id = message.from_user.id, text=f"<b>❗️ <u>ɪᴍᴘᴏʀᴛᴀɴᴛ</u> ❗️</b>\n\n<b>ᴛʜᴇꜱᴇ ᴠɪᴅᴇᴏꜱ / ꜰɪʟᴇꜱ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ</b> <b><u>10 ᴍɪɴᴜᴛᴇꜱ</u> </b><b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ).</b>\n\n<b><i>📌 ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜᴇꜱᴇ ᴠɪᴅᴇᴏꜱ / ꜰɪʟᴇꜱ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ.</i></b>")
        await asyncio.sleep(600)
        for x in filesarr:
            await x.delete()
        await k.edit_text("<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏꜱ / ꜰɪʟᴇꜱ ᴀʀᴇ ᴅᴇʟᴇᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ !\nᴋɪɴᴅʟʏ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>")
        return
    elif data.startswith("files"):
        # print('file is asking again to bypass url shortner')
        user_id = message.from_user.id
        if temp.SHORT.get(user_id)==None:
            return await message.reply_text(text="<b>Please Search Again in Group</b>")
        else:
            chat_id = temp.SHORT.get(user_id)
        settings = await get_settings(chat_id)
        if not await db.has_prime_status(user_id) and settings['url_mode']:
            files_ = await get_file_details(file_id)
            files = files_[0]
            generatedurl = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")
            k = await client.send_message(chat_id=message.from_user.id,text=f"🫂 ʜᴇʏ {message.from_user.mention}\n\n✅ ʏᴏᴜʀ ʟɪɴᴋ ɪꜱ ʀᴇᴀᴅʏ, ᴋɪɴᴅʟʏ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴜᴛᴛᴏɴ.\n\n🎁 ꜰɪʟᴇ ɴᴀᴍᴇ : <code>{files.file_name}</code> \n\n⚕ ꜰɪʟᴇ ꜱɪᴢᴇ : <code>{get_size(files.file_size)}</code>\n\n", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton('📁 ᴅᴏᴡɴʟᴏᴀᴅ 📁', url=generatedurl)
                        ],[
                            InlineKeyboardButton('✨ ʙᴜʏ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ : ʀᴇᴍᴏᴠᴇ ᴀᴅꜱ ✨', callback_data="seeplans")                            
                        ]
                    ]
                )
            )
            await asyncio.sleep(600)
            await k.edit("<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ !\nᴋɪɴᴅʟʏ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>")
            return
    files_ = await get_file_details(file_id)           
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        try:
            # Create the inline keyboard button with callback_data
            button = InlineKeyboardButton('▶ Gen Stream / Download Link', callback_data=f'generate_stream_link:{file_id}')
            # Create the inline keyboard markup with the button
            keyboard = InlineKeyboardMarkup([[button]])
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                reply_markup=keyboard,
                protect_content=True if pre == 'filep' else False,
                )
            filetype = msg.media
            file = getattr(msg, filetype.value)
            title = file.file_name
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return
            await msg.edit_caption(f_caption)
            btnll = [[
            InlineKeyboardButton("❗ ɢᴇᴛ ꜰɪʟᴇ ᴀɢᴀɪɴ ❗", callback_data=f'delfile#{file_id}')
                        ]]
            lost = await client.send_message(chat_id = message.from_user.id, text=f"<b>⚠ <u>warning ⚠</u> </b>\n\n<b>ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ</b> <b><u>30 ᴍɪɴᴜᴛᴇꜱ</u> </b><b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ).</b>\n\n<b><i>📌 ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ.</i></b>")
            await asyncio.sleep(1800)
            await msg.delete()
            await lost.edit_text("<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b>",reply_markup=InlineKeyboardMarkup(btnll))
            return
        except:
            pass
        return await message.reply('No such file exist.')
    files = files_[0]
    title = files.file_name
    size=get_size(files.file_size)
    f_caption=files.caption
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            logger.exception(e)
            f_caption=f_caption
    if f_caption is None:
        f_caption = f"{files.file_name}"

    button = InlineKeyboardButton('▶ Gen Stream / Download Link', callback_data=f'generate_stream_link:{file_id}')
    # Create the inline keyboard markup with the button
    keyboard = InlineKeyboardMarkup([[button]])
    lazy_file = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        reply_markup=keyboard,  # Use the created keyboard
        protect_content=True if pre == 'filep' else False,
        )
    btnl = [[
                InlineKeyboardButton("❗ ɢᴇᴛ ꜰɪʟᴇ ᴀɢᴀɪɴ ❗", callback_data=f'delfile#{file_id}')
                ]]
    lzzz = await client.send_message(chat_id = message.from_user.id, text=f"<b>⚠ <u>warning ⚠</u> </b>\n\n<b>ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ</b> <b><u>30 ᴍɪɴᴜᴛᴇꜱ</u> </b><b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ).</b>\n\n<b><i>📌 ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ.</i></b>")
    await asyncio.sleep(1800)
    await lazy_file.delete()
    await lzzz.edit_text("<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b>",reply_markup=InlineKeyboardMarkup(btnl))


@Client.on_message(filters.command('channels') & filters.user(ADMINS))
async def channel_info(bot, message):
           
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Bhkk!! Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)
 
@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))

@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return
    
    file_id, file_ref = unpack_new_file_id(media.file_id)

    result = await Media.collection.delete_one({
        '_id': file_id,
    })
    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count:
            await msg.edit('File is successfully deleted from database')
        else:
            # files indexed before https://github.com/LazyDeveloperr/lazyPrincess/commit/f3d2a1bcb155faf44178e5d7a685a1b533e714bf#diff-86b613edf1748372103e94cacff3b578b36b698ef9c16817bb98fe9ef22fb669R39 
            # have original file name.
            result = await Media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count:
                await msg.edit('File is successfully deleted from database')
            else:
                await msg.edit('File not found in database')

@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        'This will delete all indexed files.\nDo you want to continue??',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="YES", callback_data="autofilter_delete"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="CANCEL", callback_data="close_data"
                    )
                ],
            ]
        ),
        quote=True,
    )

@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, message):
    await Media.collection.drop()
    await message.answer('♥️ Thank You LazyDeveloper ♥️')
    await message.message.edit('Succesfully Deleted All The Indexed Files.')

@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are anonymous admin. Use /connect {message.chat.id} in PM")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return

    settings = await get_settings(grp_id)
    
    if 'url_mode' not in settings.keys():
        await save_group_settings(grp_id, 'url_mode', False)
    else:
        pass
    if settings is not None:
        buttons = [
            [
                InlineKeyboardButton('URL Mode',
                                     callback_data=f'setgs#url_mode#{settings["url_mode"]}#{str(grp_id)}'),
                InlineKeyboardButton('✅ Yes' if settings["url_mode"] else '❌ No',
                                         callback_data=f'setgs#url_mode#{settings["url_mode"]}#{str(grp_id)}')
            ],[
                InlineKeyboardButton(
                    'Filter Button',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Single' if settings["button"] else 'Double',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Bot PM',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ Yes' if settings["botpm"] else '❌ No',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'File Secure',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ Yes' if settings["file_secure"] else '❌ No',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'IMDB',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ Yes' if settings["imdb"] else '❌ No',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Spell Check',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ Yes' if settings["spell_check"] else '❌ No',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Welcome',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ Yes' if settings["welcome"] else '❌ No',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(buttons)

        await message.reply_text(
            text=f"<b>Change Your Settings for {title} As Your Wish ⚙</b>",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
            reply_to_message_id=message.id
        )

@Client.on_message(filters.command('set_template'))
async def save_template(client, message):
    sts = await message.reply("Checking template")
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are anonymous admin. Use /connect {message.chat.id} in PM")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return

    if len(message.command) < 2:
        return await sts.edit("No Input!!")
    template = message.text.split(" ", 1)[1]
    await save_group_settings(grp_id, 'template', template)
    await sts.edit(f"Successfully changed template for {title} to\n\n{template}")

@Client.on_message(filters.command("add_prime") & filters.user(ADMINS))
async def add_prime_status(client, message):
    try:
        if len(message.command) == 4:
            time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
            current_time = time_zone.strftime("%d-%m-%Y\n⏱️ Joining time : %I:%M:%S %p") 
            user_id = int(message.command[1])  # Convert the user_id to integer
            user = await client.get_users(user_id)
            time = message.command[2]+" "+message.command[3]
            seconds = await get_seconds(time)
            if seconds > 0:
                expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
                user_data = {"id": user_id, "expiry_time": expiry_time}  # Using "id" instead of "user_id"  
                await db.update_user(user_data)  # Use the update_user method to update or insert user data
                data = await db.get_user(user_id)
                expiry = data.get("expiry_time")   
                expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")         
                await message.reply_text(f"{user.mention} Added to Prime list ✅\n\n👤 Name : {user.mention}\n⚡ ID : <code>{user_id}</code>\n⏰ Limit : <code>{time}</code>\n\n⏳ Joining Date : {current_time}\n\n⌛️ Exp Date : {expiry_str_in_ist}", disable_web_page_preview=True)
                await client.send_message(
                    chat_id=user_id,
                    text=f"👋 ʜᴇʏ {user.mention},\nThank you for purchasing prime membership.\n\n⏰ LIMIT : <code>{time}</code>\n⏳ Joining Date : {current_time}\n\n⌛️ Exp Date : {expiry_str_in_ist}", disable_web_page_preview=True              
                )
                await client.send_message(PRIME_MEMBERS_LOGS, text=f"#New Prime member \n\n👤 Name : {user.mention}\n⚡ ID : <code>{user_id}</code>\n⏰ LIMIT : <code>{time}</code>\n\n⏳ Joining Date : {current_time}\n\n⌛️ Exp Date : {expiry_str_in_ist}", disable_web_page_preview=True)

            else:
                await message.reply_text("Invalid time format. Please use '1 day for days', '1 hour for hours', or '1 min for minutes', or '1 month for months' or '1 year for year'")
        else:
            await message.reply_text("Usage : /add_prime user_id time (e.g., '1 day for days', '1 hour for hours', or '1 min for minutes', or '1 month for months' or '1 year for year')")
    except Exception as e:
        print(e)
        
@Client.on_message(filters.command("remove_prime") & filters.user(ADMINS))
async def remove_prime(client, message):
    if len(message.command) == 2:
        user_id = int(message.command[1])  # Convert the user_id to integer
        user = await client.get_users(user_id)
        if await db.remove_prime_status(user_id):
            await message.reply_text("User removed  successfully! ✔")
            await client.send_message(
                chat_id=user_id,
                text=f"<b>ʜᴇʏ {user.mention},\n\nʏᴏᴜʀ ᴘʀɪᴍᴇ ᴀᴄᴄᴇss ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ.\nᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴜsɪɴɢ ᴏᴜʀ sᴇʀᴠɪᴄᴇ 😊\nᴄʟɪᴄᴋ ᴏɴ /plan ᴛᴏ ᴄʜᴇᴄᴋ ᴏᴜᴛ ᴏᴛʜᴇʀ ᴘʟᴀɴꜱ.</b>"
            )
        else:
            await message.reply_text("ᴜɴᴀʙʟᴇ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴜꜱᴇʀ !\nᴀʀᴇ ʏᴏᴜ ꜱᴜʀᴇ, ɪᴛ ᴡᴀꜱ ᴀ ᴘʀɪᴍᴇ ᴜꜱᴇʀ ɪᴅ ?")
    else:
        await message.reply_text("ᴜꜱᴀɢᴇ : /remove_prime user_id") 

@Client.on_message(filters.command("get_prime") & filters.user(ADMINS))
async def get_prime_status(client, message):
    if len(message.command) == 2:
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        data = await db.get_user(user_id)  # Convert the user_id to integer
        if data and data.get("expiry_time"):
            #expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=data)
            expiry = data.get("expiry_time") 
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")            
            # Calculate time difference
            current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
            time_left = expiry_ist - current_time
            
            # Calculate days, hours, and minutes
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # Format time left as a string
            time_left_str = f"{days} days, {hours} hours, {minutes} minutes"
            await message.reply_text(f"⚜️ ᴘʀɪᴍᴇ ᴜꜱᴇʀ ᴅᴀᴛᴀ :\n\n👤 ᴜꜱᴇʀ : {user.mention}\n⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ ᴛɪᴍᴇ ʟᴇꜰᴛ : {time_left_str}\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}")
        else:
            await message.reply_text("ɴᴏ ᴀɴʏ ᴘʀɪᴍᴇ ᴅᴀᴛᴀ ᴡᴀꜱ ꜰᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ !")
    else:
        await message.reply_text("ᴜꜱᴀɢᴇ : /get_prime user_id")

@Client.on_message(filters.command("prime_users") & filters.user(ADMINS))
async def prime_user(client, message):
    aa = await message.reply_text("<i>Please wait...</i>")
    new = f"⚜️ ᴘʀɪᴍᴇ ᴜꜱᴇʀꜱ ʟɪꜱᴛ :\n\n"
    user_count = 1

    try:
        users = await db.get_all_users()
        logging.debug(f"Fetched {len(users)} users")
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        await aa.edit_text("Failed to fetch users.")
        return

    async for user in users:
        try:
            data = await db.get_user(user['id'])
            logging.debug(f"Fetched data for user {user['id']}: {data}")
            
            if data and data.get("expiry_time"):
                expiry = data.get("expiry_time")
                expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
                expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")
                current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
                time_left = expiry_ist - current_time
                days = time_left.days
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_left_str = f"{days} days, {hours} hours, {minutes} minutes"
                
                new += f"{user_count}. {(await client.get_users(user['id'])).mention}\n👤 ᴜꜱᴇʀ ɪᴅ : {user['id']}\n⏳ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}\n⏰ ᴛɪᴍᴇ ʟᴇꜰᴛ : {time_left_str}\n"
                user_count += 1
        except Exception as e:
            logging.error(f"Error processing user {user['id']}: {e}")
            continue

    try:
        await aa.edit_text(new)
    except MessageTooLong:
        with open('usersplan.txt', 'w+') as outfile:
            outfile.write(new)
        await message.reply_document('usersplan.txt', caption="Paid Users:")
    except Exception as e:
        logging.error(f"Error editing message: {e}")
        await aa.edit_text("Failed to send the user list.")

@Client.on_message(filters.command("myplan"))
async def myplan(client, message):
    user = message.from_user.mention 
    user_id = message.from_user.id
    data = await db.get_user(message.from_user.id)  # Convert the user_id to integer
    if data and data.get("expiry_time"):
        #expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=data)
        expiry = data.get("expiry_time") 
        expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
        expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")            
        # Calculate time difference
        current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        time_left = expiry_ist - current_time
            
        # Calculate days, hours, and minutes
        days = time_left.days
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
            
        # Format time left as a string
        time_left_str = f"{days} ᴅᴀʏꜱ, {hours} ʜᴏᴜʀꜱ, {minutes} ᴍɪɴᴜᴛᴇꜱ"
        await message.reply_text(f"👑 ᴘʀɪᴍᴇ ᴜꜱᴇʀ ᴅᴀᴛᴀ :\n\n👤 Name : {user}\n⚡ ID : <code>{user_id}</code>\n⏰ Time Left : {time_left_str}\n⌛️ Exp Date : {expiry_str_in_ist}")   
    else:
        await message.reply_text(f"ʜᴇʏ {user},\n\nʏᴏᴜ ᴅᴏ ɴᴏᴛ ʜᴀᴠᴇ ᴀɴʏ ᴀᴄᴛɪᴠᴇ ᴘʀɪᴍᴇ ᴘʟᴀɴs, ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴛᴀᴋᴇ ᴘʀɪᴍᴇ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ 👇",
	reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 ᴄʜᴇᴄᴋᴏᴜᴛ ᴘʀɪᴍᴇ ᴘʟᴀɴꜱ 💸", callback_data='seeplans')]]))			 

@Client.on_message(filters.command("plan"))
async def plan(client, message):
    user_id = message.from_user.id 
    users = message.from_user.mention 
    btn = [[
	
        InlineKeyboardButton("📲 ꜱᴇɴᴅ ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ ʜᴇʀᴇ", url=f"https://t.me/{ADMIN_USRNM}")],[InlineKeyboardButton("❌ ᴄʟᴏꜱᴇ ❌", callback_data="close_data")
    ]]
    await message.reply_photo(photo="https://graph.org/file/55a5392f88ec5a4bd3379.jpg", caption=script.PLANS_TXT.format(message.from_user.mention, UPI_ID, QR_CODE_IMG), reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("shortlink"))
async def shortlink(bot, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ'ʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ, ᴛᴜʀɴ ᴏꜰꜰ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ᴀɴᴅ ᴛʀʏ ᴛʜɪꜱ ᴀɢᴀɪɴ ᴄᴏᴍᴍᴀɴᴅ.")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention}, ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴏɴʟʏ ᴡᴏʀᴋꜱ ɪɴ ɢʀᴏᴜᴘꜱ !")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    data = message.text
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return await message.reply_text("<b>ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀᴄᴄᴇꜱꜱ ᴛᴏ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ !\nᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴏɴʟʏ ᴡᴏʀᴋꜱ ꜰᴏʀ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴꜱ.</b>")
    else:
        pass
    try:
        command, shortlink_url, api = data.split(" ")
    except:
        return await message.reply_text("<b>ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ !\nɢɪᴠᴇ ᴍᴇ ᴄᴏᴍᴍᴀɴᴅ ᴀʟᴏɴɢ ᴡɪᴛʜ ꜱʜᴏʀᴛɴᴇʀ ᴡᴇʙꜱɪᴛᴇ ᴀɴᴅ ᴀᴘɪ.\n\nꜰᴏʀᴍᴀᴛ : <code>/shortlink krishnalink.com c8dacdff6e91a8e4b4f093fdb4d8ae31bc273c1a</code>")
    reply = await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
    shortlink_url = re.sub(r"https?://?", "", shortlink_url)
    shortlink_url = re.sub(r"[:/]", "", shortlink_url)
    await save_group_settings(grpid, 'shortlink', shortlink_url)
    await save_group_settings(grpid, 'shortlink_api', api)
    await save_group_settings(grpid, 'url_mode', True)
    await reply.edit_text(f"<b>✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴀᴅᴅᴇᴅ ꜱʜᴏʀᴛʟɪɴᴋ ꜰᴏʀ <code>{title}</code>.\n\nꜱʜᴏʀᴛʟɪɴᴋ ᴡᴇʙꜱɪᴛᴇ : <code>{shortlink_url}</code>\nꜱʜᴏʀᴛʟɪɴᴋ ᴀᴘɪ : <code>{api}</code></b>")

@Client.on_message(filters.command("setshortlinkoff") & filters.user(ADMINS))
async def offshortlink(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋꜱ ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘꜱ !")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    await save_group_settings(grpid, 'url_mode', False)
    ENABLE_SHORTLINK = False
    return await message.reply_text("ꜱʜᴏʀᴛʟɪɴᴋ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅɪꜱᴀʙʟᴇᴅ.")
    
@Client.on_message(filters.command("setshortlinkon") & filters.user(ADMINS))
async def onshortlink(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋꜱ ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘꜱ !")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    await save_group_settings(grpid, 'url_mode', True)
    ENABLE_SHORTLINK = True
    return await message.reply_text("ꜱʜᴏʀᴛʟɪɴᴋ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴇɴᴀʙʟᴇᴅ.")

@Client.on_message(filters.command("shortlink_info"))
async def ginfo(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>{message.from_user.mention},\n\nᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ.</b>")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    chat_id=message.chat.id
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
 
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return await message.reply_text("<b>ᴏɴʟʏ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴏʀ ᴀᴅᴍɪɴ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ !</b>")
    else:
        settings = await get_settings(chat_id) #fetching settings for group
        if 'shortlink' in settings.keys() and 'tutorial' in settings.keys():
            su = settings['shortlink']
            sa = settings['shortlink_api']
            st = settings['tutorial']
            return await message.reply_text(f"<b><u>ᴄᴜʀʀᴇɴᴛ  ꜱᴛᴀᴛᴜꜱ<u> 📊\n\nᴡᴇʙꜱɪᴛᴇ : <code>{su}</code>\n\nᴀᴘɪ : <code>{sa}</code>\n\nᴛᴜᴛᴏʀɪᴀʟ : {st}</b>", disable_web_page_preview=True)
        elif 'shortlink' in settings.keys() and 'tutorial' not in settings.keys():
            su = settings['shortlink']
            sa = settings['shortlink_api']
            return await message.reply_text(f"<b><u>ᴄᴜʀʀᴇɴᴛ  ꜱᴛᴀᴛᴜꜱ<u> 📊\n\nᴡᴇʙꜱɪᴛᴇ : <code>{su}</code>\n\nᴀᴘɪ : <code>{sa}</code>\n\nᴜꜱᴇ /set_tutorial ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ꜱᴇᴛ ʏᴏᴜʀ ᴛᴜᴛᴏʀɪᴀʟ.")
        elif 'shortlink' not in settings.keys() and 'tutorial' in settings.keys():
            st = settings['tutorial']
            return await message.reply_text(f"<b>ᴛᴜᴛᴏʀɪᴀʟ : <code>{st}</code>\n\nᴜꜱᴇ  /shortlink  ᴄᴏᴍᴍᴀɴᴅ  ᴛᴏ  ᴄᴏɴɴᴇᴄᴛ  ʏᴏᴜʀ  ꜱʜᴏʀᴛɴᴇʀ</b>")
        else:
            return await message.reply_text("ꜱʜᴏʀᴛɴᴇʀ ᴀɴᴅ ᴛᴜᴛᴏʀɪᴀʟ ᴀʀᴇ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ.\n\nᴄʜᴇᴄᴋ /set_tutorial  ᴀɴᴅ  /shortlink  ᴄᴏᴍᴍᴀɴᴅ.")


@Client.on_message(filters.command("set_tutorial"))
async def settutorial(bot, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"I did'nt recognise you as an admin. Try again ")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("This command works only in group")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return
    else:
        pass
    if len(message.command) == 1:
        return await message.reply("<b>ɢɪᴠᴇ ᴍᴇ ᴀ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ ᴀʟᴏɴɢ ᴡɪᴛʜ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ.\n\nᴜꜱᴀɢᴇ : /set_tutorial <code>https://t.me/LazyTutorialLink/23</code></b>")
    elif len(message.command) == 2:
        reply = await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
        tutorial = message.command[1]
        await save_group_settings(grpid, 'tutorial', tutorial)
        await save_group_settings(grpid, 'is_tutorial', True)
        await reply.edit_text(f"<b>Tutorial added successfully ✔\n\nʏᴏᴜʀ ɢʀᴏᴜᴘ : {title}\n\nʏᴏᴜʀ ᴛᴜᴛᴏʀɪᴀʟ : <code>{tutorial}</code></b>")
    else:
        return await message.reply("<b>ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ ɪɴᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ !\nᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ : /set_tutorial <code>https://t.me/LazyTutorialLink/23</code></b>")

@Client.on_message(filters.command("remove_tutorial"))
async def removetutorial(bot, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"I did'nt recognise you as an admin. Please Try Again")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("This command only works in group !")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return
    else:
        pass
    reply = await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
    await save_group_settings(grpid, 'is_tutorial', False)
    await reply.edit_text(f"<b>Tutorial link removed ✔</b>")

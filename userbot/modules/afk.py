# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module which contains afk-related commands """

import time

from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import (UpdateProfileRequest)

from telethon.events import StopPropagation
from userbot import (BOTLOG, BOTLOG_CHATID, CMD_HELP, COUNT_MSG, USERS,
                     is_redis_alive, bot)
from userbot.events import register, grp_exclude
from userbot.modules.dbhelper import afk, afk_reason, is_afk, is_gone, no_afk


# @register(incoming=True, disable_edited=True, disable_errors=True)
# @grp_exclude()
# async def mention_afk(mention):
#     """ This function takes care of notifying the
#      people who mention you that you are AFK."""
#
#     global COUNT_MSG
#     global USERS
#     if not is_redis_alive():
#         return
#
#     IsGone = await is_gone()
#
#     if IsGone is True:
#         return
#
#     IsAway = await is_afk()
#     if mention.message.mentioned and not (await mention.get_sender()).bot:
#         if IsAway is True:
#             Reason = await afk_reason()
#             Message = "I am an Auto-Reply Bot, my boss is currently away from Telegram but will respond to your message promptly upon return."
#
#             if Reason != "no reason":
#                 Message = Message + "\n\nReason: ```" + Reason + "```"
#
#             if mention.sender_id not in USERS:
#                 await mention.reply(Message)
#                 USERS.update({mention.sender_id: 1})
#                 COUNT_MSG = COUNT_MSG + 1
#             elif mention.sender_id in USERS:
#                 if USERS[mention.sender_id] % 40 == 0:
#                     await mention.reply("I am an Auto-Reply Bot, my boss is still AFK from his desk.")
#                     USERS[mention.sender_id] = USERS[mention.sender_id] + 1
#                     COUNT_MSG = COUNT_MSG + 1
#                 else:
#                     USERS[mention.sender_id] = USERS[mention.sender_id] + 1
#                     COUNT_MSG = COUNT_MSG + 1


@register(incoming=True, disable_errors=True)
@grp_exclude()
async def afk_on_pm(afk_pm):
    global USERS
    global COUNT_MSG
    if not is_redis_alive():
        return

    IsGone = await is_gone()

    if IsGone is True:
        return

    IsAway = await is_afk()
    if afk_pm.is_private and not (await afk_pm.get_sender()).bot:
        if IsAway is True:
            Reason = await afk_reason()
            Message = "I am an Auto-Reply Bot, my boss is currently away from Telegram but will respond to your message promptly upon return."

            if Reason != "no reason":
                Message = Message + "\n\nReason: ```" + Reason + "```"

            if afk_pm.sender_id not in USERS:
                await afk_pm.reply(Message)
                USERS.update({afk_pm.sender_id: 1})
                COUNT_MSG = COUNT_MSG + 1
            elif afk_pm.sender_id in USERS:
                if USERS[afk_pm.sender_id] % 50 == 0:
                    await afk_pm.reply(Message)
                    USERS[afk_pm.sender_id] = USERS[afk_pm.sender_id] + 1
                    COUNT_MSG = COUNT_MSG + 1
                else:
                    USERS[afk_pm.sender_id] = USERS[afk_pm.sender_id] + 1
                    COUNT_MSG = COUNT_MSG + 1


@register(outgoing=True, disable_errors=True, pattern="^.afk")
@grp_exclude()
async def set_afk(setafk):
    if not is_redis_alive():
        await setafk.edit("`Database connections failing!`")
        return
    message = setafk.text
    try:
        AFKREASON = str(message[5:])
    except BaseException:
        AFKREASON = ''
    if not AFKREASON:
        AFKREASON = 'no reason'
    await setafk.delete()
    if BOTLOG:
        await setafk.client.send_message(BOTLOG_CHATID, "You went AFK!")
    await afk(AFKREASON)

    replied_user = await get_user(setafk)
    firstname = "[AFK] " + replied_user.user.first_name
    lastname = replied_user.user.last_name

    await bot(
        UpdateProfileRequest(
            first_name=firstname,
            last_name=lastname
        )
    )

    raise StopPropagation


@register(outgoing=True, disable_errors=True)
@grp_exclude(force_exclude=True)
async def type_afk_is_not_true(notafk):
    global COUNT_MSG
    global USERS
    if not is_redis_alive():
        return
    IsAway = await is_afk()
    if IsAway is True:
        await no_afk()

        replied_user = await get_user(notafk)

        firstname = replied_user.user.first_name.replace("[AFK] ", "")
        lastname = replied_user.user.last_name

        await bot(
            UpdateProfileRequest(
                first_name=firstname,
                last_name=lastname
            )
        )

        if BOTLOG:
            await notafk.client.send_message(
                BOTLOG_CHATID,
                "You've recieved " + str(COUNT_MSG) + " messages from " +
                str(len(USERS)) + " chats while you were away",
            )
            for i in USERS:
                name = await notafk.client.get_entity(i)
                name0 = str(name.first_name)
                await notafk.client.send_message(
                    BOTLOG_CHATID,
                    "[" + name0 + "](tg://user?id=" + str(i) + ")" +
                    " sent you " + "`" + str(USERS[i]) + " messages`",
                )
        COUNT_MSG = 0
        USERS = {}


async def get_user(event):
    """ Get the user from argument or replied message. """
    if event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        replied_user = await event.client(
            GetFullUserRequest(previous_message.from_id))
    else:
        self_user = await event.client.get_me()
        user = self_user.id

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(probable_user_mention_entity,
                          MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                replied_user = await event.client(GetFullUserRequest(user_id))
                return replied_user
        try:
            user_object = await event.client.get_entity(user)
            replied_user = await event.client(
                GetFullUserRequest(user_object.id))
        except (TypeError, ValueError) as err:
            await event.edit(str(err))
            return None

    return replied_user


CMD_HELP.update({
    "afk": [
        'AFK',
        " - `.afk <reason> (optional)`: Sets your status as AFK. Responds to anyone who tags/PM's "
        "you telling you are AFK. Switches off AFK when you type back anything."
        "Can't be used when using actively `.gone <reason>`"
    ]
})

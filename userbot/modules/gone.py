# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module which contains gone-related commands """

import time

from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import (UpdateProfileRequest)

from telethon.events import StopPropagation
from userbot import (BOTLOG, BOTLOG_CHATID, CMD_HELP, COUNT_MSG, USERS,
                     is_redis_alive, bot)
from userbot.events import register, grp_exclude
from userbot.modules.dbhelper import gone, gone_reason, is_gone, no_gone


@register(incoming=True, disable_edited=True, disable_errors=True)
@grp_exclude()
async def mention_gone(mention):
    """ This function takes care of notifying the
     people who mention you that you are GONE."""

    global COUNT_MSG
    global USERS
    if not is_redis_alive():
        return

    IsAway = await is_gone()

    printf(mention)

    if mention.message.mentioned and not (await mention.get_sender()).bot:
        if IsAway is True:
            Reason = await gone_reason()
            Message = "I am an Auto-Reply Bot, my boss is currently not there from his desk but will respond to your message promptly upon return"

            if Reason != "no reason":
                Message = Message + "\n\nReason: ```" + Reason + "```"

            if mention.sender_id not in USERS:
                await mention.reply(Message)
                USERS.update({mention.sender_id: 1})
                COUNT_MSG = COUNT_MSG + 1
            elif mention.sender_id in USERS:
                if USERS[mention.sender_id] % 10 == 0:
                    await mention.reply("I am an Auto-Reply Bot, my boss is still not there from his desk.")
                    USERS[mention.sender_id] = USERS[mention.sender_id] + 1
                    COUNT_MSG = COUNT_MSG + 1
                else:
                    USERS[mention.sender_id] = USERS[mention.sender_id] + 1
                    COUNT_MSG = COUNT_MSG + 1


@register(incoming=True, disable_errors=True)
@grp_exclude()
async def gone_on_pm(gone_pm):
    global USERS
    global COUNT_MSG
    if not is_redis_alive():
        return

    IsAway = await is_gone()
    if gone_pm.is_private and not (await gone_pm.get_sender()).bot:
        if IsAway is True:
            Reason = await gone_reason()
            Message = "I am an Auto-Reply Bot, my boss is currently not there from his desk but will respond to your message promptly upon return"

            if Reason != "no reason":
                Message = Message + "\n\nReason: ```" + Reason + "```"

            if gone_pm.sender_id not in USERS:
                await gone_pm.reply(Message)
                USERS.update({gone_pm.sender_id: 1})
                COUNT_MSG = COUNT_MSG + 1
            elif gone_pm.sender_id in USERS:
                if USERS[gone_pm.sender_id] % 10 == 0:
                    await gone_pm.reply(Message)
                    USERS[gone_pm.sender_id] = USERS[gone_pm.sender_id] + 1
                    COUNT_MSG = COUNT_MSG + 1
                else:
                    USERS[gone_pm.sender_id] = USERS[gone_pm.sender_id] + 1
                    COUNT_MSG = COUNT_MSG + 1


@register(outgoing=True, disable_errors=True, pattern="^.gone")
@grp_exclude()
async def set_gone(setgone):
    if not is_redis_alive():
        await setgone.edit("`Database connections failing!`")
        return
    message = setgone.text
    try:
        GONEREASON = str(message[5:])
    except BaseException:
        GONEREASON = ''
    if not GONEREASON:
        GONEREASON = 'no reason'
    await setgone.delete()
    if BOTLOG:
        await setgone.client.send_message(BOTLOG_CHATID, "You went GONE!")
    await gone(GONEREASON)

    replied_user = await get_user(setgone)
    firstname = "[GONE] " + replied_user.user.first_name.replace("[AFK] ", "")
    lastname = replied_user.user.last_name

    await bot(
        UpdateProfileRequest(
            first_name=firstname,
            last_name=lastname
        )
    )

    raise StopPropagation


@register(outgoing=True, pattern="^.back$")
@grp_exclude()
async def back(event):
    global COUNT_MSG
    global USERS
    if not is_redis_alive():
        return

    IsAway = await is_gone()
    if IsAway is True:
        await no_gone()

        await event.delete()

        replied_user = await get_user(event)

        firstname = replied_user.user.first_name.replace("[GONE] ", "")
        lastname = replied_user.user.last_name

        await bot(
            UpdateProfileRequest(
                first_name=firstname,
                last_name=lastname
            )
        )

        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "You've recieved " + str(COUNT_MSG) + " messages from " +
                str(len(USERS)) + " chats while you were away",
            )
            for i in USERS:
                name = await event.client.get_entity(i)
                name0 = str(name.first_name)
                await event.client.send_message(
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
    "gone": [
        'GONE',
        " - `.gone <reason> (optional)`: Sets your status as gone. Responds to anyone who tags/PM's "
        "you telling you are gone. Switches off gone when you type `.back`."
    ],
    "back": [
        'BACK',
        " - `.back`: Switches off `.gone` status."
    ]
})

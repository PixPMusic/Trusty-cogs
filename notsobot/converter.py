import re
from typing import List, Pattern, Union

import discord
import unidecode
from discord.ext.commands.converter import Converter
from discord.ext.commands.errors import BadArgument
from redbot.core import commands

IMAGE_LINKS: Pattern = re.compile(
    r"(https?:\/\/[^\"\'\s]*\.(?:png|jpg|jpeg|gif|png|svg)(\?size=[0-9]*)?)", flags=re.I
)
EMOJI_REGEX: Pattern = re.compile(r"(<(a)?:[a-zA-Z0-9\_]+:([0-9]+)>)")
MENTION_REGEX: Pattern = re.compile(r"<@!?([0-9]+)>")
ID_REGEX: Pattern = re.compile(r"[0-9]{17,}")


class ImageFinder(Converter):
    """
    This is a class to convert notsobots image searching capabilities
    into a more general converter class
    """

    async def convert(
        self, ctx: commands.Context, argument: str
    ) -> List[Union[discord.Asset, str]]:
        attachments = ctx.message.attachments
        mentions = MENTION_REGEX.finditer(argument)
        matches = IMAGE_LINKS.finditer(argument)
        emojis = EMOJI_REGEX.finditer(argument)
        ids = ID_REGEX.finditer(argument)
        urls = []
        if matches:
            for match in matches:
                urls.append(match.group(1))
        if emojis:
            for emoji in emojis:
                ext = "gif" if emoji.group(2) else "png"
                url = "https://cdn.discordapp.com/emojis/{id}.{ext}?v=1".format(
                    id=emoji.group(3), ext=ext
                )
                urls.append(url)
        if mentions:
            for mention in mentions:
                if ctx.guild:
                    user = ctx.guild.get_member(int(mention.group(1)))
                else:
                    user = ctx.bot.get_user(int(mention.group(1)))
                if user is None:
                    continue
                if user.display_avatar.is_animated():
                    urls.append(user.display_avatar.replace(format="gif").url)
                else:
                    urls.append(user.display_avatar.replace(format="png").url)
        if not urls and ids:
            for possible_id in ids:
                if ctx.guild:
                    user = ctx.guild.get_member(int(possible_id.group(1)))
                else:
                    user = ctx.bot.get_user(int(possible_id.group(1)))
                if user:
                    if user.display_avatar.is_animated():
                        urls.append(user.display_avatar.replace(format="gif").url)
                    else:
                        urls.append(user.display_avatar.replace(format="png").url)
        if attachments:
            for attachment in attachments:
                urls.append(attachment.url)
        if not urls:
            for m in ctx.guild.members:
                if argument.lower() in unidecode.unidecode(m.display_name.lower()):
                    # display_name so we can get the nick of the user first
                    # without being NoneType and then check username if that matches
                    # what we're expecting
                    urls.append(m.display_avatar.replace(format="png").url)
                    continue
                if argument.lower() in unidecode.unidecode(m.name.lower()):
                    urls.append(m.display_avatar.replace(format="png").url)
                    continue

        if not urls:
            raise BadArgument("No images provided.")
        return urls

    async def search_for_images(
        self, ctx: commands.Context
    ) -> List[Union[discord.Asset, discord.Attachment, str]]:
        urls = []
        if not ctx.channel.permissions_for(ctx.me).read_message_history:
            raise BadArgument("I require read message history perms to find images.")
        async for message in ctx.channel.history(limit=10):
            if message.attachments:
                for attachment in message.attachments:
                    urls.append(attachment)
            match = IMAGE_LINKS.match(message.content)
            if match:
                urls.append(match.group(1))
        if not urls:
            raise BadArgument("No Images found in recent history.")
        return urls

import discord
import os
from datetime import datetime, timedelta
from pytz import timezone
from langchain.memory import ChatMessageHistory
from openai_service import get_openai_response, judge_if_i_response

intents = discord.Intents.all()
discord_key = os.environ['DISCORD_KEY']
allowed_channels = [1090678631489077331, 1134007804244529212, 1133743935727091773]
master_id = 576031815945420812

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.states = {}

    async def on_ready(self):
        print('Bot is ready.')
        print('Logged in as', self.user)

    async def on_message(self, message):
        if message.channel.id not in allowed_channels:
            return

        # Get the server's ID
        server_id = message.guild.id

        # If this server's state is not initialized yet, initialize it
        if server_id not in self.states:
            self.states[server_id] = {
                "history": ChatMessageHistory(),
                "count": 0,
                "current_date": datetime.now(timezone('Europe/Warsaw')).date(),
            }

        # Get this server's state
        state = self.states[server_id]

        auther_name = ''
        if master_id == message.author.id:
            auther_name = 'マスター'
        elif message.author.nick:
            auther_name = message.author.nick
        else:
            auther_name = message.author.name

        print('Message received from', auther_name, ':', message.content)

        # don't respond to ourselves
        if message.author == self.user:
            print('Message received from self, ignoring.')
            return
        if state["count"] > 100:
            print('Message limit.')
            return

        # ユーザーメッセージを会話履歴に追加
        state["history"].add_user_message(auther_name + ": " + message.content)
        print("User:", message.content)

        if judge_if_i_response(state["history"]):
            # Check if date has changed
            new_date = datetime.now(timezone('Europe/Warsaw')).date()
            if new_date > state["current_date"]:
                state["count"] = 0
                state["current_date"] = new_date

            model_name = "gpt-4" if state["count"] <= 20 else "gpt-3.5-turbo"
            response = get_openai_response(state["history"], model_name)
            await message.channel.send(response)

            state["count"] += 1
            print('Message send completed.')
        else:
            print('Message not recognized.')

client = MyClient(intents=intents)
client.run(discord_key)

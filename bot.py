import asyncio
import math
import os
import random
import re
import sqlite3
import threading
import urllib.parse
import urllib.request
import datetime
from subprocess import Popen, PIPE, STDOUT
from threading import Timer
from time import sleep

import discord
import requests
from discord import Client
from discord import Game, VoiceClient
from discord import Intents
from pytube import YouTube
from pytube.exceptions import RegexMatchError
from pytz import timezone

TOKEN = ''  # Your token goes here
OWNER_ID = ''  # Here goes your discord id

MINECRAFT_SERVER_PATH = './minecraft/server.jar'
running = False
starting = False
process = None

intents = Intents.default()
intents.members = True
client = Client(intents=intents)
# server - channel - voice client - songs_to_play
voice_clients = {}


class CustomException(Exception):
    def __init__(self):
        pass


@client.event
async def on_message(msg):

    global running
    global starting
    global process

    guild_id = msg.guild.id

    connection = sqlite3.connect('database.sqlite')
    cursor = connection.cursor()

    if msg.author == client.user:
        return
    else:
        if len(msg.content) > 4:
            # Level-up system
            cursor.execute('''CREATE TABLE
                              IF NOT EXISTS
                              users (server_id int, user_id int, experience int, user_level int,
                              PRIMARY KEY (server_id, user_id))''')
            cursor.execute(f'''SELECT * FROM users WHERE server_id == {guild_id} AND user_id == {msg.author.id}''')
            found = False
            for date in cursor.fetchall():
                found = True
                experience = date[2]
                user_level = date[3]
                experience += 1
                if is_level_up(experience, user_level):
                    user_level += 1
                    await msg.channel.send(f'Congratulations {msg.author.mention}, you are now level {user_level}!')
                cursor.execute(f'''UPDATE users
                                   SET experience = {experience}, user_level = {user_level}
                                   WHERE server_id == {guild_id} AND user_id == {msg.author.id}
                                   ''')
                connection.commit()
            if not found:
                cursor.execute(f'''INSERT INTO users VALUES ({guild_id}, {msg.author.id}, 1, 0)''')
                connection.commit()

    # Get level
    if msg.content.startswith(".level") or msg.content.startswith(".lvl"):
        cursor.execute(f'''SELECT experience, user_level FROM users
        WHERE server_id={guild_id} AND user_id = {msg.author.id} ''')
        found = False
        for user in cursor.fetchall():
            found = True
            embed_var = discord.Embed(title=msg.author.display_name, color=0xff0000)
            embed_var.add_field(name="User experience: ", value=user[0], inline=False)
            embed_var.add_field(name="User level: ", value=user[1], inline=False)
            await msg.channel.send(embed=embed_var)
        if not found:
            cursor.execute('''CREATE TABLE
                              IF NOT EXISTS
                              users (server_id int, user_id int, experience int, user_level int,
                              PRIMARY KEY (server_id, user_id))''')
            cursor.execute(f'''INSERT INTO users VALUES ({guild_id}, {msg.author.id}, 0, 0)''')
            for user in cursor.fetchall():
                embed_var = discord.Embed(title=msg.author.display_name, color=0xff0000)
                embed_var.add_field(name="User experience: ", value=user[0], inline=False)
                embed_var.add_field(name="User level: ", value=user[1], inline=False)
                await msg.channel.send(embed=embed_var)
            await msg.content.send("You don't have any levels yet dear user. You can gain levels and experience by "
                                   "**sending messages** and **being active** in the server.")

    # Random message
    if msg.content.startswith(".rmsg") or msg.content.startswith(".rmessage") or msg.content.startswith(".rms"):
        messages = [
            'What a lovely day!'
        ]
        await msg.channel.send(random.choice(messages))

    # Hello
    elif msg.content.startswith(".hello") or msg.content.startswith(".hi") or msg.content.startswith(".hey"):
        msg_send = "Hello " + msg.author.mention + "!"
        await msg.channel.send(msg_send)

    # Bye
    elif msg.content.startswith(".bye") or msg.content.startswith(".cya") or msg.content.startswith(".goodbye"):
        msg_send = "Goodbye " + msg.author.mention + "!"
        await msg.channel.send(msg_send)

    # Get date
    elif msg.content.startswith(".date") or msg.content.startswith(".time") or msg.content.startswith(".datetime"):
        await msg.channel.send(f"These are the current date and time: "
                               f"{datetime.datetime.now(tz=timezone('Europe/Ljubljana')).strftime('%d.%m.%Y - %H:%M:%S')}")

    # Kill
    elif msg.content.startswith(".kill"):
        split_msg = msg.content.split(" ")
        split_msg = (filter("".__ne__, split_msg))
        split_msg = [i for i in split_msg]
        sp_methods = ["murdered",
                      "killed"]
        c_methods = ["killed himself.",
                     "committed suicide.",
                     "committed sepuku."]
        if len(split_msg) > 1:
            if random.randint(0, 1) == 1:
                target = split_msg[1]
                await msg.channel.send(f"{msg.author.mention} {random.choice(sp_methods)} {target}.")
            else:
                target = split_msg[1]
                await msg.channel.send(f"{msg.author.mention} failed at killing {target}.")
        else:
            await msg.channel.send(f"{msg.author.mention} {random.choice(c_methods)}.")

    # Sqrt
    elif msg.content.startswith(".sqrt") or msg.content.startswith("._/"):
        split_msg = msg.content.split(" ")
        split_msg = (filter("".__ne__, split_msg))
        split_msg = [i for i in split_msg]
        number = split_msg[1]
        if number is not None:
            try:
                number = float(number)
                _sqrt = math.sqrt(number)
                send_msg = 'Square root of {0} is {1} {2}'.format(number, _sqrt, msg.author.mention)
                await msg.channel.send(send_msg)
            except ValueError:
                await msg.channel.send('Please enter a number {0}'.format(msg.author.mention))
        else:
            await msg.channel.send('Enter a number after the command (!sqrt 16.7) {0}'.format(msg.author.mention))

    # Dice
    elif msg.content.startswith(".dice"):
        split_msg = msg.content.split(" ")
        split_msg = (filter("".__ne__, split_msg))
        split_msg = [i for i in split_msg]
        if len(split_msg) > 1:
            try:
                first = 1
                second = int(split_msg[1])
                send_msg = '{0} threw {1}!'.format(msg.author.mention, str(random.randint(first, second)))
                await msg.channel.send(send_msg)
            except ValueError:
                await msg.channel.send('Please enter a number {0}'.format(msg.author.mention))
        else:
            await msg.channel.send('{0} threw {1}!'.format(msg.author.mention, str(random.randint(1, 6))))

    # Bitcoin
    elif msg.content.startswith(".bitcoin") or msg.content.startswith(".btc"):
        url = 'https://api.coindesk.com/v1/bpi/currentprice/BTC.json'
        response = requests.get(url)
        value = response.json()['bpi']['USD']['rate']
        await msg.channel.send('Bitcoin value is: {0}$'.format(value))

    # Poll
    elif msg.content.startswith(".poll "):
        args = []
        in_word = False
        word = ""
        description = msg.content[6:]

        # Parse the input
        for s in description.split(" "):
            s = s.rstrip()
            s = s.lstrip()
            if s == "":
                continue
            if "\"" in s:

                if s[0] == "\"" and s[len(s) - 1] == "\"":
                    args.append(s[1:-1])
                elif not in_word:
                    word += s[1:] + " "
                    in_word = True
                else:
                    word += s[:-1]
                    in_word = False
                    args.append(word)
                    word = ""
            elif in_word:
                word += s + " "
            else:
                args.append(s)
        if word != "" and word != " ":
            args.append(word)

        text = ""
        opts = []
        emojis = '🟥🟧🟨🟩🟦🟪⬛🟫⬜🔴🟠🟡🟢🔵🟣⚫⚪🟤'
        if args is not None:
            try:
                if len(args) > 1:
                    passed = False
                    for arg in args:
                        if not passed:
                            text += arg
                            passed = True
                        else:
                            opts.append(arg)
                    for i in range(0, len(opts)):
                        text += '\n' + emojis[i] + ' - ' + opts[i]
                    _message = await msg.channel.send(text)
                    for i in range(0, len(opts)):
                        await _message.add_reaction(emojis[i])
            except IndexError:
                await msg.channel.send("Too many option added, add less.")
            except:
                await msg.channel.send("Something went wrong, try again.")

    # Get exams
    elif msg.content.startswith(".exam") or msg.content.startswith(".t") or msg.content.startswith(".test") \
            or msg.content.startswith(".tst"):
        # Create table if not exists
        # Create table if not exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS exams
                          (server_id int, subject String, years int, hours int, minutes int, days int, months int,
                           content String,
                          PRIMARY KEY (server_id, subject, years, months, days, hours, minutes, content))''')
        # Get the data
        cursor.execute(f'''SELECT subject, years, months, days, hours, minutes, content FROM exams
                           WHERE server_id = {guild_id}
                           ORDER BY years, months, days, hours, minutes, subject, content''')
        message = "```"
        c = 0
        for exam in cursor.fetchall():
            if not below_current_date_year(exam[1], exam[2], exam[3], exam[4], exam[5]):
                c += 1
                line = f"{c} | {exam[0]} | {exam[4]}:{exam[5]} | {exam[3]}.{exam[2]}.{exam[1]} | {exam[6]}|"
                message += line + "\n"
            else:
                cursor.execute(f'''DELETE FROM exams WHERE server_id = {guild_id} AND subject = "{exam[0]}"
                                    AND years = {exam[1]} AND hours = {exam[4]} AND minutes = {exam[5]}
                                    AND days = {exam[3]} AND months = {exam[2]} AND content = "{exam[6]}"
                                    ''')
                connection.commit()

        if message == "```":
            await msg.channel.send("**No upcoming tests**")
        else:
            await msg.channel.send("> **These are the upcoming exams:**\n" + message + "```")

    # Remove exam
    elif msg.content.startswith(".rmt") or msg.content.startswith(".remove_exam") or msg.content.startswith(".rmtest")\
            or msg.content.startswith(".rme") or msg.content.startswith(".rt") or msg.content.startswith(".re") or \
            msg.content.startswith(".rmexam"):
        split_msg = msg.content.split(" ")
        split_msg = (filter("".__ne__, split_msg))
        split_msg = [i for i in split_msg]
        if len(split_msg) == 2:
            # Create table if not exists
            cursor.execute('''CREATE TABLE IF NOT EXISTS exams
                              (server_id int, subject String, years int, months int, days int, hours int, minutes int,
                             content String,
                             PRIMARY KEY (server_id, subject, years, months, days, hours, minutes, content))''')
            # Get the data
            cursor.execute(f'''SELECT subject, years, months, days, hours, minutes, content FROM exams
                               WHERE server_id = {guild_id}
                               ORDER BY years, months, days, hours, minutes, subject, content''')
            try:
                c = int(split_msg[1])
                for exam in cursor.fetchall():
                    if c > 1:
                        c -= 1
                        continue
                    elif c == 1:
                        cursor.execute(f'''
                        DELETE FROM exams WHERE server_id = {guild_id} AND subject = "{exam[0]}"
                         AND years = {exam[1]} AND hours = {exam[4]} AND minutes = {exam[5]} AND days = {exam[3]}
                         AND months = {exam[2]} AND content = "{exam[6]}"
                        ''')
                        connection.commit()
                        await msg.channel.send("Exam removed!")
                        break
                    else:
                        await msg.channel.send("Index out of bounds.")
            except ValueError:
                await msg.channel.send("Please enter the correct parameters -> .rmt [index] -> example: .rmt 2")

        elif len(split_msg) <= 1:
            await msg.channel.send("To few arguments, please add the index of the homework that you want removed"
                                   " -> .rmt [index] -> example: .rmt 2")
        else:
            await msg.channel.send("To many arguments, please only add the index of the homework that you want removed"
                                   " -> .rmt [index] -> example: .rmt 2")

    # Save exam
    elif msg.content.startswith(".save_exam") or msg.content.startswith(".st") or msg.content.startswith(".stest"):

        # Subject -  time -  date - content
        split_content = msg.content.split(" ")
        split_content = (filter("".__ne__, split_content))
        split_content = [i for i in split_content]
        if len(split_content) >= 5:
            split_content = split_content[1:]
            subject_name = split_content[0]
            time = split_content[1]
            date = split_content[2]

            # Check time
            if len(time) == 5:
                try:
                    if time[2] != ":":
                        raise ValueError()
                    hour = int(time[:2])
                    minute = int(time[3:])
                    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                        raise CustomException

                    # Date
                    if len(date) == 5:
                        try:
                            if date[2] != ".":
                                raise ValueError()
                            day = int(date[:2])
                            month = int(date[3:])
                            # Check date validity
                            if not 0 < month < 13:
                                raise CustomException
                            if month in [1, 3, 5, 7, 8, 10, 12]:
                                if not 0 < day < 32:
                                    raise CustomException
                            elif month == 2:
                                if not 0 < day < 29:
                                    raise CustomException
                            else:
                                if not 0 < day < 31:
                                    raise CustomException

                            # Content
                            content = ""
                            description = split_content[3:]
                            if description[0].rstrip()[0] == "\"" and description[0].rstrip()[len(description[0]) - 1]\
                                    == "\"":
                                content = description[0][1:-1]
                            elif len(description) > 1:
                                for s in split_content[3:]:
                                    content += s.strip('"') + " "
                            else:
                                content = description[0] + " "

                            # Save the exam in the database
                            # Create table if not exists
                            cursor.execute('''
                            CREATE TABLE IF NOT EXISTS exams
                            (server_id int, subject String, years int, months int, days int, hours int, minutes int,
                             content String,
                             PRIMARY KEY (server_id, subject, years, months, days, hours, minutes, content))''')
                            # Save the exam
                            try:
                                # Getting the correct date
                                current_year = int(datetime.datetime.now().strftime("%Y"))
                                if below_current_date(month, day, hour, minute):
                                    current_year += 1

                                cursor.execute(f'''
                                INSERT INTO exams 
                                VALUES ({guild_id}, "{subject_name}", {current_year}, {month}, {day}, {hour}, {minute},
                                 "{content}")
                                ''')
                                await msg.channel.send("Exam saved!")
                            except sqlite3.IntegrityError:
                                await msg.channel.send("This exam already exists!")
                            # Commit
                            connection.commit()

                        except ValueError:
                            await msg.channel.send("Wrong date format, enter the date like this: 20.11 or 01.05")
                        except CustomException:
                            await msg.channel.send("Invalid date")
                    else:
                        await msg.channel.send("Wrong date format, enter the date like this: 20.11 or 01.05")

                except ValueError:
                    await msg.channel.send("Wrong time format, enter the time like this: 20:13 or 01:00")
                except CustomException:
                    await msg.channel.send("Invalid time")
            else:
                await msg.channel.send("Wrong time format, enter the time like this: 20:13 or 01:00")

        else:
            await msg.channel.send("Not enough arguments")

    # Get homeworks
    elif msg.content.startswith(".homework") or msg.content.startswith(".hw"):
        # Create table if not exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS homeworks
                          (server_id int, subject String, years int, hours int, minutes int, days int, months int,
                           content String,
                          PRIMARY KEY (server_id, subject, years, months, days, hours, minutes, content))''')
        # Get the data
        cursor.execute(f'''SELECT subject, years, months, days, hours, minutes, content FROM homeworks
                           WHERE server_id = {guild_id}
                           ORDER BY years, months, days, hours, minutes, subject, content''')
        message = "```"
        c = 0
        for exam in cursor.fetchall():
            if not below_current_date_year(exam[1], exam[2], exam[3], exam[4], exam[5]):
                c += 1
                line = f"{c} | {exam[0]} | {exam[4]}:{exam[5]} | {exam[3]}.{exam[2]}.{exam[1]} | {exam[6]}|"
                message += line + "\n"
            else:
                cursor.execute(f'''DELETE FROM homeworks WHERE server_id = {guild_id} AND subject = "{exam[0]}"
                                    AND years = {exam[1]} AND hours = {exam[4]} AND minutes = {exam[5]}
                                    AND days = {exam[3]} AND months = {exam[2]} AND content = "{exam[6]}"
                                    ''')
                connection.commit()

        if message == "```":
            await msg.channel.send("**There is no homework**")
        else:
            await msg.channel.send("> **This is the homework that needs to be done:**\n" + message + "```")

    # Save homework
    elif msg.content.startswith(".save_homework") or msg.content.startswith(".shw"):

        # Subject -  time -  date - content
        split_content = msg.content.split(" ")
        split_content = (filter("".__ne__, split_content))
        split_content = [i for i in split_content]
        if len(split_content) >= 5:
            split_content = split_content[1:]
            subject_name = split_content[0]
            time = split_content[1]
            date = split_content[2]

            # Check time
            if len(time) == 5:
                try:
                    if time[2] != ":":
                        raise ValueError()
                    hour = int(time[:2])
                    minute = int(time[3:])
                    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                        raise CustomException

                    # Date
                    if len(date) == 5:
                        try:
                            if date[2] != ".":
                                raise ValueError()
                            day = int(date[:2])
                            month = int(date[3:])
                            # Check date validity
                            if not 0 < month < 13:
                                raise CustomException
                            if month in [1, 3, 5, 7, 8, 10, 12]:
                                if not 0 < day < 32:
                                    raise CustomException
                            elif month == 2:
                                if not 0 < day < 29:
                                    raise CustomException
                            else:
                                if not 0 < day < 31:
                                    raise CustomException

                            # Content
                            content = ""
                            description = split_content[3:]
                            if description[0].rstrip()[0] == "\"" and description[0].rstrip()[len(description[0]) - 1] \
                                    == "\"":
                                content = description[0][1:-1]
                            elif len(description) > 1:
                                for s in split_content[3:]:
                                    content += s.strip('"') + " "
                            else:
                                content = description[0] + " "

                            # Save the homework in the database
                            # Create table if not exists
                            cursor.execute('''
                            CREATE TABLE IF NOT EXISTS homeworks
                            (server_id int, subject String, years int, months int, days int, hours int, minutes int,
                             content String,
                             PRIMARY KEY (server_id, subject, years, months, days, hours, minutes, content))''')
                            # Save the homework
                            try:
                                # Getting the correct date
                                current_year = int(datetime.datetime.now().strftime("%Y"))
                                if below_current_date(month, day, hour, minute):
                                    current_year += 1

                                cursor.execute(f'''
                                INSERT INTO homeworks 
                                VALUES ({guild_id}, "{subject_name}", {current_year}, {month}, {day}, {hour}, {minute},
                                 "{content}")
                                ''')
                                await msg.channel.send("Homework saved!")
                            except sqlite3.IntegrityError:
                                await msg.channel.send("This homework already exists!")
                            # Commit
                            connection.commit()

                        except ValueError:
                            await msg.channel.send("Wrong date format, enter the date like this: 20.11 or 01.05")
                        except CustomException:
                            await msg.channel.send("Invalid date")
                    else:
                        await msg.channel.send("Wrong date format, enter the date like this: 20.11 or 01.05")

                except ValueError:
                    await msg.channel.send("Wrong time format, enter the time like this: 20:13 or 01:00")
                except CustomException:
                    await msg.channel.send("Invalid time")
            else:
                await msg.channel.send("Wrong time format, enter the time like this: 20:13 or 01:00")

        else:
            await msg.channel.send("Not enough arguments")

    # Remove homework
    elif msg.content.startswith(".rmhw") or msg.content.startswith(".remove_homework") or\
            msg.content.startswith(".rhw"):
        split_msg = msg.content.split(" ")
        split_msg = (filter("".__ne__, split_msg))
        split_msg = [i for i in split_msg]
        if len(split_msg) == 2:
            # Create table if not exists
            cursor.execute('''CREATE TABLE IF NOT EXISTS homeworks
                              (server_id int, subject String, years int, months int, days int, hours int, minutes int,
                             content String,
                             PRIMARY KEY (server_id, subject, years, months, days, hours, minutes, content))''')
            # Get the data
            cursor.execute(f'''SELECT subject, years, months, days, hours, minutes, content FROM homeworks
                               WHERE server_id = {guild_id}
                               ORDER BY years, months, days, hours, minutes, subject, content''')
            try:
                c = int(split_msg[1])
                for hw in cursor.fetchall():
                    if c > 1:
                        c -= 1
                        continue
                    elif c == 1:
                        cursor.execute(f'''
                        DELETE FROM homeworks WHERE server_id = {guild_id} AND subject = "{hw[0]}"
                         AND years = {hw[1]} AND hours = {hw[4]} AND minutes = {hw[5]} AND days = {hw[3]}
                         AND months = {hw[2]} AND content = "{hw[6]}"
                        ''')
                        connection.commit()
                        await msg.channel.send("Homework removed!")
                        break
                    else:
                        await msg.channel.send("Index out of bounds.")
            except ValueError:
                await msg.channel.send("Please enter the correct parameters -> .rmt [index] -> example: .rmt 2")

        elif len(split_msg) <= 1:
            await msg.channel.send("To few arguments, please add the index of the homework that you want removed"
                                   " -> .rmt [index] -> example: .rmt 2")
        else:
            await msg.channel.send("To many arguments, please only add the index of the homework that you want removed"
                                   " -> .rmt [index] -> example: .rmt 2")

    # Easter egg
    elif msg.content.startswith(".bot"):
        await msg.channel.send("Yes, I am a robot, what else did you think I am: "
                               "https://www.youtube.com/watch?v=fsF7enQY8uI")

    # Playing music
    elif msg.content.startswith(".p") or msg.content.startswith(".play"):

        # Args
        args = msg.content.split(" ")
        args = (filter("".__ne__, args))
        args = [i for i in args]

        if len(args) > 1:

            arg = ""
            for _arg in args[1:]:
                arg += _arg

            # Add a new voice client if not exists
            if guild_id not in voice_clients:
                user = msg.author
                channel = user.voice.channel
                await channel.connect()
                guild = msg.guild
                voice_client: VoiceClient = discord.utils.get(client.voice_clients, guild=guild)
                voice_clients[guild_id] = [guild_id, channel, voice_client, []]
            else:
                guild_id, channel, voice_client, ignored = voice_clients[guild_id]
                if not voice_client.is_connected():
                    try:
                        voice_client.stop()
                    except:
                        pass
                    del voice_clients[guild_id]
                    user = msg.author
                    channel = user.voice.channel
                    await channel.connect()
                    guild = msg.guild
                    voice_client: VoiceClient = discord.utils.get(client.voice_clients, guild=guild)
                    voice_clients[guild_id] = [guild_id, channel, voice_client, []]

            # Search for the song on youtube if needed
            if len(args) == 2:
                if not ("www.youtube.com" in arg or "youtu.be" in arg):
                    arg = yt_search(arg)
            else:
                arg = yt_search(arg)

            # Add the song to query
            await add_to_que(arg, guild_id, msg)

            await play_next_song(guild_id)

        else:
            msg.channel.send("Missing arguments")

    # Skipping a song
    elif msg.content.startswith(".skip") or msg.content.startswith(".next"):
        guild_id, channel, voice_client, ignored = voice_clients[guild_id]
        if voice_client.is_playing():
            await msg.channel.send("**Skipped the song.**")
            voice_client.stop()
            await play_next_song(guild_id)
            await msg.delete()
        else:
            await msg.channel.send("**Cannot skip, no song playing.**")

    # Disconnecting the bot from the voice channel
    elif msg.content.startswith(".fuckoff") or msg.content.startswith(".exit") or msg.content.startswith(".quit") or\
            msg.content.startswith(".getout") or msg.content.startswith(".disconnect"):
        guild_id, channel, voice_client, ignored = voice_clients[guild_id]
        await voice_client.voice_disconnect()
        await msg.channel.send("Goodbye!")
        del voice_clients[guild_id]

    # Starting the minecraft server
    elif msg.content.startswith(".mcstart"):
        if str(msg.author.id) == OWNER_ID:
            if not running and not starting:
                eula_gen()
                process = Popen(["java", "-jar", "-Xmx4096M", "-Xms2048M", MINECRAFT_SERVER_PATH, "--nogui"], stdout=PIPE,
                                stdin=PIPE, stderr=STDOUT)
                starting = True
                await msg.channel.send("*Server starting...*")
                thread = threading.Thread(target=terminal_output)
                thread.start()
                c = 0
                while True:
                    sleep(1)
                    c += 1
                    if c > 30:
                        await msg.channel.send("*Could not start the server...*")
                        running = False
                        starting = False
                        break
                    if running:
                        await msg.channel.send("**Server started!**")
                        break
            elif running:
                await msg.channel.send("The server is running!")
            else:
                await msg.channel.send("Server is starting!")
        else:
            await msg.channel.send("Sorry, only the owner can run this command.")

    # Stopping the minecraft server
    elif msg.content.startswith(".mcstop"):
        if str(msg.author.id) == OWNER_ID:
            if running and not starting:
                await msg.channel.send("*Stopping the server...*")
                process.communicate(input=b"stop")
                process.wait()
                running = False
                await msg.channel.send("**Server stopped!**")
            elif not running:
                await msg.channel.send("Server is not running!")
            else:
                await msg.channel.send("Server is starting!")
        else:
            await msg.channel.send("Sorry, only the owner can run this command.")

    # Getting the server IP
    elif msg.content.startswith(".mcip"):
        if running:
            await msg.channel.send("**IP:** davidblog.si")
        else:
            await msg.channel.send("Server is not running!")

    # Server status
    elif msg.content.startswith(".mcstatus"):
        if running:
            await msg.channel.send("*The server is running.*")
        else:
            await msg.channel.send("*The server is not running.*")

    # Server backup
    elif msg.content.startswith(".mcbackup"):
        if str(msg.author.id) == OWNER_ID:
            if not running and not starting:
                await msg.channel.send("*Backing up...*")
                folder_name = f'{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}_world'
                os.system('mkdir backups')
                os.system(f'mkdir ./backups/{folder_name}')
                os.system(f'cp -avr ./world ./backups/{folder_name}')
                await msg.channel.send("**Backup complete!**")
            else:
                await msg.channel.send("The server is running, cannot back up.")
        else:
            await msg.channel.send("Sorry, only the owner can run this command.")

    # Help
    elif msg.content.startswith(".help"):
        message = "> **Info:**\n```" \
                  "When passing multi-word arguments as one argument, please wrap the argument with quotation" \
                  " marks like this: (\"This is an argument\").\n" \
                  "A star sign * before the argument means, that the argument is optional: *[argument].\n" \
                  "A star sing * in the argument means, that the argument can consist of multiple words:" \
                  " [*argument].```\n" \
                  "> **Commands list:**\n```" \
                  ".rmsg      - Sends a random message\n" \
                  "           * Usage: .rmsg\n" \
                  "           $ Aliases: [.rmsg, .rmessage, .rms]\n" \
                  ".hi        - Greets the user\n" \
                  "           * Usage: .hi\n" \
                  "           $ Aliases: [.hello, .hi, .hey]\n" \
                  ".bye       - Says goodbye to the user\n" \
                  "           * Usage: .bye\n" \
                  "           $ Aliases: [.bye, .cya, .goodbye]\n" \
                  ".sqrt      - Calculates the square root of a given number\n" \
                  "           * Usage: .sqrt [number]\n" \
                  "           $ Aliases: [.sqrt, ._/]\n" \
                  ".dice      - Throw a dice\n" \
                  "           * Usage: .dice *[number_of_dice_sides]\n" \
                  "           $ Aliases: [.dice]\n" \
                  ".bitcoin   - Get the current bitcoin value\n" \
                  "           * Usage: .bitcoin\n" \
                  "           $ Aliases: [.bitcoin, .btc]\n" \
                  ".poll      - Creates a poll\n" \
                  "           * Usage: .poll [text] [*options]\n" \
                  "           $ Aliases: [.poll]\n" \
                  ".exam      - Lists the upcoming exams\n" \
                  "           * Usage: .exam\n" \
                  "           $ Aliases: [.exam, .t, .test, .tst]\n" \
                  ".save_exam - Saves the exam\n" \
                  "           * Usage: .save_exam [subject] [hour:minute] [day.month] [*content]\n" \
                  "           + [*content] -> Can be provided without quotation marks\n" \
                  "           $ Aliases: [.save_exam, .st, .stest]\n" \
                  ".rme       - Removes a test from the list\n" \
                  "           * Usage: .rmt [index]\n" \
                  "           $ Aliases: [.rmt, .remove_exam, .rmtest, .rmexam, .rme, .rt, .re]\n" \
                  ".homework  - Lists the upcoming homework\n" \
                  "           * Usage: .homework\n" \
                  "           $ Aliases: [.homework, .hw]\n" \
                  "```"
        await msg.channel.send(message)
        message = "```" +\
                  ".shw       - Saves the homework\n" \
                  "           * Usage: .shw [subject] [hour:minute] [day.month] [*content]\n" \
                  "           + [*content] -> Can be provided without quotation marks\n" \
                  "           $ Aliases: [.shw, .save_homework]\n" \
                  ".rhw       - Removes a homework from the list\n" \
                  "           * Usage: .rhw [index]\n" \
                  "           $ Aliases: [.rmhw, .remove_homework, .rhw]\n" \
                  ".level     - Shows the user level\n" \
                  "           * Usage: .level\n" \
                  "           & Aliases: [.level, .lvl]\n" \
                  "```\n" \
                  "> **Experimental features:**\n" \
                  "*These features are experimental and thus they may not function properly or " \
                  "may be very slow. Use them with caution.*\n" \
                  "```" \
                  ".play      - Plays music from youtube\n" \
                  "           * Usage: .play [youtube_link]\n" \
                  "           $ Aliases: [.play, .p]\n" \
                  ".skip      - Skips a song\n" \
                  "           * Usage: .skip\n" \
                  "           $ Aliases: [.skip, .next]\n" \
                  ".quit      - Disconnects from the voice channel\n" \
                  "           * Usage: .quit\n" \
                  "           $ Aliases: [.quit, .exit, .fuckoff, .getout, .disconnect]" \
                  "```\n" \
                  "> **Minecraft server:**\n" \
                  "*Certain commands are reserved only for the owner.*\n" \
                  "```" \
                  ".mcstart   - Starts the minecraft server\n" \
                  "           * Usage: .mcstart\n" \
                  "           $ Aliases: [.mcstart]\n" \
                  ".mcstop    - Stops the minecraft server\n" \
                  "           * Usage: .mcstop\n" \
                  "           $ Aliases: [.mcstop]\n" \
                  ".mcip      - Displays the ip of the server\n" \
                  "           * Usage: .mcip\n" \
                  "           $ Aliases: [.mcip]\n" \
                  ".mcstatus  - Displays the server status\n" \
                  "           * Usage: .mcstatus\n" \
                  "           $ Aliases: [.mcstatus]\n" \
                  ".mcbackup  - Makes a server backup\n" \
                  "           * Usage: .mcbackup\n" \
                  "           $ Aliases: [.mcbackup]" \
                  "```"
        await msg.channel.send(message)

    else:
        pass

    cursor.close()


@client.event
async def on_ready():
    await client.change_presence(activity=Game(name="with .help"))
    print("Logged in as " + client.user.name)


async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed():
        print("Guilds:")
        for guild in client.guilds:
            print(" -", guild.name + ":")
            for member in guild.members:
                print("  >", member)
        await asyncio.sleep(3600)


async def play_next_song(guild_id):
    def next_song(passed_guild_id):
        if passed_guild_id in voice_clients:
            passed_guild_id, channel, voice_client, songs = voice_clients[passed_guild_id]
            if songs:
                if not voice_client.is_playing():
                    if voice_client.is_connected():
                        audio_source = discord.FFmpegPCMAudio("./songs/" + songs[0] + ".mp3",
                                                              executable="C:\\ffmpeg\\bin\\ffmpeg.exe")
                        #  On Linux remove the executable path

                        songs.remove(songs[0])
                        voice_clients[passed_guild_id] = passed_guild_id, channel, voice_client, songs
                        voice_client.play(audio_source, after=lambda e: next_song(passed_guild_id))
    next_song(guild_id)


async def download_if_not_exists(file_name, url, msg):
    if not file_name + ".mp3" in os.listdir("./songs/"):
        try:
            download_msg = await msg.channel.send("*Attempting to download the song...*")
            yt = YouTube(url)
            try:
                yt.streams.filter(only_audio=True).first().download(filename=file_name)
            except AttributeError:
                try:
                    yt.streams.filter(only_audio=True).last().download(filename=file_name)
                except AttributeError:
                    try:
                        yt.streams.filter(only_audio=True).get_audio_only().download(filename=file_name)
                    except AttributeError:
                        raise CustomException
            os.rename(file_name + ".mp4", "./songs/" + file_name + ".mp3")
            await msg.channel.send(f"{url} **added to the que.**")
            await msg.delete()
            await download_msg.delete()
            return True
        except RegexMatchError:
            await msg.channel.send("**Invalid youtube url!**")
            return False
        except CustomException:
            await msg.channel.send("**Cannot play this song.**")
            await msg.delete()
            return False
    await msg.channel.send(f"{url} **added to the que.**")
    await msg.delete()
    return True


def yt_search(search):
    query_string = urllib.parse.urlencode({'search_query': search})
    htm_content = urllib.request.urlopen('http://www.youtube.com/results?' + query_string)
    search_results = re.findall(r'/watch\?v=(.{11})', htm_content.read().decode())
    return "https://www.youtu.be/" + search_results[0]


async def add_to_que(arg, guild_id, msg):
    # server - channel - voice client - songs_to_play

    # Parsing the arguments
    url = arg

    # Downloading the song if needed
    file_name = format_word(url)
    valid_song = await download_if_not_exists(file_name, url, msg)
    if valid_song:
        voice_clients[guild_id][3].append(file_name)


def format_word(value):
    value = "".join(x for x in value if x.isalnum())
    return value


def is_level_up(experience, level):
    if experience > 10 and level < 1:
        return True
    elif experience > 50 and level < 2:
        return True
    elif experience > 200 and level < 3:
        return True
    elif experience > 500 and level < 4:
        return True
    elif experience > 1000 and level < 5:
        return True
    elif experience > 2000 and level < 6:
        return True
    elif experience > 5000 and level < 7:
        return True
    elif experience > 10000 and level < 8:
        return True
    elif experience > 20000 and level < 9:
        return True
    elif experience > 50000 and level < 10:
        return True
    elif experience > 100000 and level < 11:
        return True
    elif experience > 500000 and level < 12:
        return True
    elif experience > 1000000 and level < 13:
        return True
    else:
        return False


def below_current_date(month, day, hour, minute):
    current_datetime = datetime.datetime.now(tz=timezone('Europe/Ljubljana'))
    current_month = int(current_datetime.strftime("%m"))
    current_day = int(current_datetime.strftime("%d"))
    current_hour = int(current_datetime.strftime("%H"))
    current_minute = int(current_datetime.strftime("%M"))
    if month > current_month:
        return False
    elif month == current_month:
        if day > current_day:
            return False
        elif day == current_day:
            if hour > current_hour:
                return False
            elif hour == current_hour:
                if minute > current_minute:
                    return False
    return True


def below_current_date_year(year, month, day, hour, minute):
    current_datetime = datetime.datetime.now(tz=timezone('Europe/Ljubljana'))
    print(year, month, day, hour, minute)
    current_year = int(current_datetime.strftime("%Y"))
    current_month = int(current_datetime.strftime("%m"))
    current_day = int(current_datetime.strftime("%d"))
    current_hour = int(current_datetime.strftime("%H"))
    current_minute = int(current_datetime.strftime("%M"))
    if year > current_year:
        return False
    elif year == current_year:
        if month > current_month:
            return False
        elif month == current_month:
            if day > current_day:
                return False
            elif day == current_day:
                if hour > current_hour:
                    return False
                elif hour == current_hour:
                    if minute > current_minute:
                        return False
    return True


# Generate EULA
def eula_gen():
    if "eula.txt" not in os.listdir():
        with open("eula.txt", "w") as file:
            file.writelines("eula=true")


def terminal_output():

    global process
    global running
    global starting

    while True:
        line = process.stdout.readline()
        if not line:
            break
        if "Done (" in ("" + line.decode()):
            starting = False
            running = True


client.loop.create_task(list_servers())
client.run(TOKEN)


class RepeatedTimer(object):
    """
    A repeater, a timer
    """
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

import asyncio

import requests
from discord import Game
from discord import Client
from discord import Intents
import random
import math
import sqlite3

TOKEN = ''
print(TOKEN)

intents = Intents.default()
intents.members = True
client = Client(intents=intents)


class CustomException(Exception):
    def __init__(self):
        pass


@client.event
async def on_message(msg):
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
                send_msg = '{0} threw {1}'.format(msg.author.mention, str(random.randint(first, second)))
                await msg.channel.send(send_msg)
            except ValueError:
                await msg.channel.send('Please enter a number {0}'.format(msg.author.mention))
        else:
            await msg.channel.send('{0} threw {1}'.format(msg.author.mention, str(random.randint(1, 6))))

    # Bitcoin
    elif msg.content.startswith(".bitcoin") or msg.content.startswith("!btc"):
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
        cursor.execute('''CREATE TABLE IF NOT EXISTS exams
                          (server_id int, subject String, hours int, minutes int, days int, months int, content String,
                          PRIMARY KEY (server_id, subject, hours, minutes, days, months, content))''')
        # Get the data
        cursor.execute(f'''SELECT subject, hours, minutes, days, months, content FROM exams
                           WHERE server_id = {guild_id}
                           ORDER BY months, days, hours, minutes, subject, content''')
        message = "```"
        c = 0
        for exam in cursor.fetchall():
            c += 1
            line = f"{c} | {exam[0]} | {exam[3]}:{exam[4]} | {exam[1]}.{exam[2]} | {exam[5]} |"
            message += line + "\n"
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
                              (server_id int, subject String, hours int, minutes int, days int, months int,
                               content String,
                              PRIMARY KEY (server_id, subject, hours, minutes, days, months, content))''')
            # Get the data
            cursor.execute(f'''SELECT subject, hours, minutes, days, months, content FROM exams
                               WHERE server_id = {guild_id}
                               ORDER BY months, days, hours, minutes, subject, content''')
            try:
                c = int(split_msg[1])
                for exam in cursor.fetchall():
                    if c > 1:
                        c -= 1
                        continue
                    elif c == 1:

                        cursor.execute(f'''
                        DELETE FROM exams WHERE server_id = {guild_id} AND subject = "{exam[0]}" AND hours = {exam[1]}
                         AND minutes = {exam[2]} AND days = {exam[3]} AND months = {exam[4]} AND content = "{exam[5]}"
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
                                content = description[1:-2]

                            # Save the exam in the database
                            # Create table if not exists
                            cursor.execute('''
                            CREATE TABLE IF NOT EXISTS exams
                            (server_id int, subject String, hours int, minutes int, days int, months int,
                             content String, 
                             PRIMARY KEY (server_id, subject, hours, minutes, days, months, content))''')
                            # Save the exam
                            try:
                                cursor.execute(f'''
                                INSERT INTO exams 
                                VALUES ({guild_id}, "{subject_name}", {hour}, {minute}, {day}, {month}, "{content}")
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
                          (server_id int, subject String, hours int, minutes int, days int, months int, content String,
                          PRIMARY KEY (server_id, subject, hours, minutes, days, months, content))''')
        # Get the data
        cursor.execute(f'''SELECT subject, hours, minutes, days, months, content FROM homeworks
                           WHERE server_id = {guild_id}
                           ORDER BY months, days, hours, minutes, subject, content''')
        message = "```"
        c = 0
        for exam in cursor.fetchall():
            c += 1
            line = f"{c} | {exam[0]} | {exam[3]}:{exam[4]} | {exam[1]}.{exam[2]} | {exam[5]} |"
            message += line + "\n"
        if message == "```":
            await msg.channel.send("**There is no homework**")
        else:
            await msg.channel.send("> **This is the homework, that needs to be done:**\n" + message + "```")

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

                            # Save the exam in the database
                            # Create table if not exists
                            cursor.execute('''
                            CREATE TABLE IF NOT EXISTS homeworks
                            (server_id int, subject String, hours int, minutes int, days int, months int,
                             content String,
                             PRIMARY KEY (server_id, subject, hours, minutes, days, months, content))''')
                            # Save the exam
                            try:
                                cursor.execute(f'''
                                INSERT INTO homeworks 
                                VALUES ({guild_id}, "{subject_name}", {hour}, {minute}, {day}, {month}, "{content}")
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
                              (server_id int, subject String, hours int, minutes int, days int, months int,
                               content String,
                              PRIMARY KEY (server_id, subject, hours, minutes, days, months, content))''')
            # Get the data
            cursor.execute(f'''SELECT subject, hours, minutes, days, months, content FROM homeworks
                               WHERE server_id = {guild_id}
                               ORDER BY months, days, hours, minutes, subject, content''')
            try:
                c = int(split_msg[1])
                for exam in cursor.fetchall():
                    if c > 1:
                        c -= 1
                        continue
                    elif c == 1:

                        cursor.execute(f'''
                        DELETE FROM homeworks WHERE server_id = {guild_id} AND subject = "{exam[0]}" AND hours = {exam[1]}
                         AND minutes = {exam[2]} AND days = {exam[3]} AND months = {exam[4]} AND content = "{exam[5]}"
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
                  ".shw       - Saves the homework\n" \
                  "           * Usage: .shw [subject] [hour:minute] [day.month] [*content]\n" \
                  "           + [*content] -> Can be provided without quotation marks\n" \
                  "           $ Aliases: [.shw, .save_homework]\n" \
                  ".rhw       - Removes a homework from the list\n" \
                  "           * Usage: .rhw [index]\n" \
                  "           $ Aliases: [.rmhw, .remove_homework, .rhw]" \
                  "```"
        await msg.channel.send(message)

    else:
        pass

    cursor.close()


@client.event
async def on_ready():
    await client.change_presence(activity=Game(name="with .help"))
    print("Logged in as " + client.user.name)


@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(f'Welcome in the server {member.name}!')


async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed():
        print("Guilds:")
        for guild in client.guilds:
            print(" -", guild.name + ":")
            for member in guild.members:
                print("  >", member)
        await asyncio.sleep(3600)


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
    else:
        return False


client.loop.create_task(list_servers())
client.run(TOKEN)

# A simple discord bot that can be used to update my website: https://huangweiran.club/LifeCalendar/

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from github import Github
from datetime import datetime
from bs4 import BeautifulSoup

load_dotenv()
github_token = os.getenv('GITHUB_TOKEN')
repo_name = os.getenv('GITHUB_REPO_NAME')

if github_token is None:
    print("Github token not found")
    exit(1)

if repo_name is None:
    print("Github repo name not found")
    exit(1)

g = Github(github_token)
repo = g.get_repo(repo_name)

intents = discord.Intents.all()
intents.members = True
intents.messages = True
intents.reactions = True
client = commands.Bot(command_prefix='!', intents=intents)

@client.command()
async def new_event(ctx):
    events = []
    today = datetime.today().strftime('%m/%d/%Y')

    # Send the initial message and wait for a response
    await ctx.send('Sure. So what events do you want to add?')
    response = await client.wait_for('message')

    # Add the first event to the list
    events.append(response.content)

    # keep asking for events until the user says 'No'
    while True:
        await ctx.send('Do you want to add another event?')
        response = await client.wait_for('message')
        if response.content.lower() == 'no':
            break
        events.append(response.content)

    await ctx.send('On a scale from 0 to 100, how would you rate your day?')
    rating = await client.wait_for('message')


    # this outer while loop is to ensure that the user can revise their input multiple times
    while True:
        # compile the generated new div and display it to the user
        events_str = '<br> '.join(events)
        new_div = f'<div date="{today}" credit="{rating.content}">{events_str}</div>'

        await ctx.send("Here is the new event you added:\n\n" + new_div)
        await ctx.send("Do you want to add this event to the calendar? (yes/no/revise)")
        response = await client.wait_for('message')

        if response.content.lower() == 'yes':
            # Read the contents of the HTML file
            file_contents = repo.get_contents('events.html')
            text = file_contents.decoded_content.decode('utf-8')

            # remove the last closing div tag
            new_contents = text.rstrip('</div>')
            new_contents += new_div + '</div>'

            # update the file
            new_contents_bytes = new_contents.encode('utf-8')
            repo.update_file('events.html', f'Update events for {today}', new_contents_bytes, file_contents.sha, branch='master')
            await ctx.send('Successfully added events for the date!')
            break

        if response.content.lower() == 'no':
            await ctx.send("Okay, I won't add it. Bye!")
            return

        if response.content.lower() == 'revise':
            while True:
                await ctx.send('Which event do you want to revise (enter the number)? (or type "done" to finish)')
                response = await client.wait_for('message')
                if response.content.lower() == 'done':
                    break
                try:
                    index = int(response.content)
                    if index < 1 or index > len(events):
                        await ctx.send(f"Invalid event number. Please enter a number between 1 and {len(events)}.")
                        continue
                    await ctx.send(f"Okay, what do you want to change event {index} to?")
                    response = await client.wait_for('message')
                    events[index - 1] = response.content
                except ValueError:
                    # if the user enters a non-integer
                    await ctx.send(f"Invalid event number. Please enter a number between 1 and {len(events)}.")
                    continue



# @client.command()
# async def revise_event(ctx):
#     events = []
#     file_contents = repo.get_contents('events.html')
#     soup


if __name__ == '__main__':
    client.run(os.getenv('DISCORD_TOKEN'))

# A simple discord bot that can be used to update my website: https://huangweiran.club/LifeCalendar/
# It can be used to add/revise/delete life events/periods.

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from github import Github
from datetime import datetime
from bs4 import BeautifulSoup
import logging
import pytz
import re

logging.basicConfig(level=logging.INFO)

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

###### utils: get verified values  ######
async def wait_for_date(ctx):
    while True:
        response = await client.wait_for('message')
        try:
            datetime.strptime(response.content, '%m/%d/%Y')
            break
        except ValueError:
            await ctx.send('Please enter a valid date in the format mm/dd/yyyy.')

    return response

async def wait_for_color(ctx):
    regex = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
    while True:
        response = await client.wait_for('message')
        if regex.match(response.content):
            break
        await ctx.send('Please enter a valid color in the format #xxxxxx.')

    return response

async def wait_for_integer(ctx, range = None):
    while True:
        response = await client.wait_for('message')
        try:
            value = int(response.content)
            if range is not None:
                if value < range[0] or value > range[1]:
                    raise ValueError
            break
        except ValueError:
            if range is None:
                await ctx.send('Please enter a valid integer.')
            else:
                await ctx.send(f'Please enter a valid integer between {range[0]} and {range[1]}.')

    return value

async def wait_for_options(ctx, options=None):
    if options is None:
        options = ['yes', 'no']

    # find in the list of options, return index if found, ask for re-enter if not found
    while True:
        try:
            response = await client.wait_for('message')
            index = options.index(response.content.lower())
            return index
        except ValueError:
            await ctx.send(f'Please enter one of the following options: {", ".join(options)}.')




# event format:
# <div date="mm/dd/yyyy" credit="xx">event A <br> event B <br> event C</div>
async def add_event(ctx, event_date):
    events = []
    response = await client.wait_for('message')  # the first event

    # Add the first event to the list
    events.append(response.content)

    # keep asking for events until the user says 'No'
    while True:
        await ctx.send('Do you want to add another event? If so, what is it? If not, type "No"')
        response = await client.wait_for('message')
        if response.content.lower() == 'no':
            break
        events.append(response.content)

    await ctx.send('On a scale from 0 to 100, how would you rate your day?')
    rating = await wait_for_integer(ctx, range=[0, 100])

    # this outer while loop is to ensure that the user can revise their input multiple times
    while True:
        # compile the generated new div and display it to the user
        events_str = '<br> '.join(events)
        new_div = f'<div date="{event_date}" credit="{rating}">{events_str}</div>'

        await ctx.send("Here is the new event you added:\n\n" + new_div)
        await ctx.send("Do you want to add this event to the calendar? (yes/no/revise)")

        choice = await wait_for_options(ctx, ['yes', 'no', 'revise'])

        if choice == 0:  # add the event
            return new_div
        elif choice == 1:  # discard the event
            await ctx.send("Okay, I won't add it. Bye!")
            return None
        else:  # revise the event
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


@client.command()
async def new_event(ctx):
    # get the time in the US/Central timezone
    tz = pytz.timezone('US/Central')
    now = datetime.now(tz)
    today = now.strftime("%m/%d/%Y")
    logging.info(f"initiated new_event by {ctx.author.name} at {now}")

    # Send the initial message and wait for a response
    await ctx.send('Sure. So what events do you want to add?')
    new_div = await add_event(ctx, today)

    if new_div is not None:
        file_contents = repo.get_contents('events.html')
        text = file_contents.decoded_content.decode('utf-8')

        # remove the last closing div tag
        new_contents = text.rstrip('</div>')
        new_contents += new_div + '</div>'

        # update the file
        new_contents_bytes = new_contents.encode('utf-8')
        repo.update_file('events.html', f'[Calendar Bot]: Update events for {today}', new_contents_bytes, file_contents.sha,
                         branch='master')
        await ctx.send('Successfully added events for the date!')


@client.command()
async def revise_event(ctx):
    await ctx.send("Please enter the date of the event to be revised (format: mm/dd/yyyy):")
    response = await wait_for_date(ctx)

    date = datetime.strptime(response.content, '%m/%d/%Y').strftime('%m/%d/%Y')

    file_contents = repo.get_contents('events.html')
    soup = BeautifulSoup(file_contents.decoded_content.decode('utf-8'), 'html.parser')

    # TODO: put the following code in command !reformat_file
    # update all date attributes to the format mm/dd/yyyy
    # the original format sometimes will lack the leading 0
    # for div in soup.find_all('div'):
    #     if 'date' in div.attrs:
    #         div['date'] = datetime.strptime(div['date'], '%m/%d/%Y').strftime('%m/%d/%Y')
    #     if 'start' in div.attrs:
    #         div['start'] = datetime.strptime(div['start'], '%m/%d/%Y').strftime('%m/%d/%Y')
    #     if 'end' in div.attrs:
    #         div['end'] = datetime.strptime(div['end'], '%m/%d/%Y').strftime('%m/%d/%Y')

    # get all the divs with a date and credit attribute
    div = soup.find_all('div', attrs={'date': date, 'credit': True})

    if len(div) == 0:
        await ctx.send("No events found for that date. Do you want to add a new event for that date? (yes/no)")
        choice = await wait_for_options(ctx, ['yes', 'no'])
        if choice == 0:
            await ctx.send('Sure. So what events do you want to add?')
            new_div = await add_event(ctx, date)
            if new_div is not None:
                # find the correct place to insert the new div
                inserted = False
                all_divs = soup.find_all('div', attrs={'date': True, 'credit': True})
                for div in all_divs:
                    if datetime.strptime(div['date'], '%m/%d/%Y') > datetime.strptime(date, '%m/%d/%Y'):
                        div.insert_before(BeautifulSoup(new_div, 'html.parser'))
                        inserted = True
                        logging.info(f"inserted new div for {date}")
                        break
                if not inserted:
                    all_divs[-1].insert_after(BeautifulSoup(new_div, 'html.parser'))
                    logging.info(f"Latest: inserted new div for {date}")
            new_contents = soup.prettify()

            # update the file
            new_contents_bytes = new_contents.encode('utf-8')
            repo.update_file('events.html', f'[Calendar Bot]: Revise events for {date}', new_contents_bytes, file_contents.sha,
                             branch='master')
            await ctx.send('Successfully added events for the date!')
            return
        elif choice == 1:
            await ctx.send("Okay, I won't add it. Bye!")
            return
    else:
        await ctx.send(f"The following events were found for {date}:\n\n{div[0]}")
        await ctx.send("Do you want to revise this event? (yes/no)")
        choice = await wait_for_options(ctx, ['yes', 'no'])
        if choice == 0:
            await ctx.send("Okay, what do you want to change it to?")
            new_div = await add_event(ctx, date)
            if new_div is not None:
                div[0].replace_with(BeautifulSoup(new_div, 'html.parser'))
                new_contents = soup.prettify()

                # update the file
                new_contents_bytes = new_contents.encode('utf-8')
                repo.update_file('events.html', f'[Calendar Bot]: Revise events for {date}', new_contents_bytes, file_contents.sha,
                                 branch='master')
                await ctx.send('Successfully revised events for the date!')
        elif choice == 1:
            await ctx.send("Okay, I won't revise it. Bye!")

@client.command()
async def delete_event(ctx):
    await ctx.send("Please enter the date of the event to be deleted (format: mm/dd/yyyy):")
    response = await wait_for_date(ctx)

    date = datetime.strptime(response.content, '%m/%d/%Y').strftime('%m/%d/%Y')

    file_contents = repo.get_contents('events.html')
    soup = BeautifulSoup(file_contents.decoded_content.decode('utf-8'), 'html.parser')

    # get all the divs with a date and credit attribute
    div = soup.find_all('div', attrs={'date': date, 'credit': True})

    if len(div) == 0:
        await ctx.send("No events found for that date. Bye!")
        return

    else:
        await ctx.send(f"The following events were found for {date}:\n\n{div[0]}")
        await ctx.send("Do you want to delete this event? (yes/no)")
        choice = await wait_for_options(ctx, ['yes', 'no'])
        if choice == 0:
            div[0].decompose()
            new_contents = soup.prettify()

            # update the file
            new_contents_bytes = new_contents.encode('utf-8')
            repo.update_file('events.html', f'[Calendar Bot]: Delete events for {date}', new_contents_bytes, file_contents.sha,
                             branch='master')
            await ctx.send('Successfully deleted events for the date!')
        elif choice == 1:
            await ctx.send("Okay, I won't delete it. Bye!")

if __name__ == '__main__':
    client.run(os.getenv('DISCORD_TOKEN'))

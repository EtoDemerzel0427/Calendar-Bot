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
    rating = await client.wait_for('message')

    # reject the rating if it's not a integer between 0 and 100 and ask for a new one
    while True:
        try:
            value = int(rating.content)
            if value < 0 or value > 100:
                raise ValueError
            break
        except ValueError:
            await ctx.send('Please enter a number between 0 and 100.')
            rating = await client.wait_for('message')

    # this outer while loop is to ensure that the user can revise their input multiple times
    while True:
        # compile the generated new div and display it to the user
        events_str = '<br> '.join(events)
        new_div = f'<div date="{event_date}" credit="{rating.content}">{events_str}</div>'

        await ctx.send("Here is the new event you added:\n\n" + new_div)
        await ctx.send("Do you want to add this event to the calendar? (yes/no/revise)")
        response = await client.wait_for('message')

        if response.content.lower() == 'yes':
            return new_div

        if response.content.lower() == 'no':
            await ctx.send("Okay, I won't add it. Bye!")
            return None

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


@client.command()
async def new_event(ctx):
    today = datetime.today().strftime('%m/%d/%Y')

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
        repo.update_file('events.html', f'Update events for {today}', new_contents_bytes, file_contents.sha,
                         branch='master')
        await ctx.send('Successfully added events for the date!')


@client.command()
async def revise_event(ctx):
    await ctx.send("Please enter the date of the event to be revised (format: mm/dd/yyyy):")
    response = await client.wait_for('message')

    # reject the date if it's not in the correct format
    while True:
        try:
            datetime.strptime(response.content, '%m/%d/%Y')
            break
        except ValueError:
            await ctx.send('Please enter a valid date in the format mm/dd/yyyy.')
            response = await client.wait_for('message')

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
        response = await client.wait_for('message')

        while True:
            if response.content.lower() == 'yes':
                await ctx.send('Sure. So what events do you want to add?')
                new_div = await add_event(ctx, date)
                if new_div is not None:
                    # find the correct place to insert the new div
                    for div in soup.find_all('div', attrs={'date': True, 'credit': True}):
                        if datetime.strptime(div['date'], '%m/%d/%Y') > datetime.strptime(date, '%m/%d/%Y'):
                            div.insert_before(BeautifulSoup(new_div, 'html.parser'))
                            break
                new_contents = soup.prettify()

                # update the file
                new_contents_bytes = new_contents.encode('utf-8')
                repo.update_file('events.html', f'Revise events for {date}', new_contents_bytes, file_contents.sha,
                                 branch='master')
                await ctx.send('Successfully added events for the date!')
                return
            elif response.content.lower() == 'no':
                await ctx.send("Okay, I won't add it. Bye!")
                return
            else:
                await ctx.send("Please enter yes or no.")
                response = await client.wait_for('message')

    else:
        await ctx.send(f"The following events were found for {date}:\n\n{div[0]}")
        await ctx.send("Do you want to revise this event? (yes/no)")
        response = await client.wait_for('message')

        while True:
            if response.content.lower() == 'yes':
                await ctx.send("Okay, what do you want to change it to?")
                new_div = await add_event(ctx, date)
                if new_div is not None:
                    div[0].replace_with(BeautifulSoup(new_div, 'html.parser'))
                    new_contents = soup.prettify()

                    # update the file
                    new_contents_bytes = new_contents.encode('utf-8')
                    repo.update_file('events.html', f'Revise events for {date}', new_contents_bytes, file_contents.sha,
                                     branch='master')
                    await ctx.send('Successfully revised events for the date!')
                return
            elif response.content.lower() == 'no':
                await ctx.send("Okay, I won't revise it. Bye!")
                return
            else:
                await ctx.send("Please enter yes or no.")
                response = await client.wait_for('message')

@client.command()
async def delete_event(ctx):
    await ctx.send("Please enter the date of the event to be deleted (format: mm/dd/yyyy):")
    response = await client.wait_for('message')

    # reject the date if it's not in the correct format
    while True:
        try:
            datetime.strptime(response.content, '%m/%d/%Y')
            break
        except ValueError:
            await ctx.send('Please enter a valid date in the format mm/dd/yyyy.')
            response = await client.wait_for('message')

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
        response = await client.wait_for('message')

        while True:
            if response.content.lower() == 'yes':
                div[0].decompose()
                new_contents = soup.prettify()

                print(new_contents)

                # update the file
                new_contents_bytes = new_contents.encode('utf-8')
                repo.update_file('events.html', f'Delete events for {date}', new_contents_bytes, file_contents.sha,
                                 branch='master')
                await ctx.send('Successfully deleted events for the date!')
                return
            elif response.content.lower() == 'no':
                await ctx.send("Okay, I won't delete it. Bye!")
                return
            else:
                await ctx.send("Please enter yes or no.")
                response = await client.wait_for('message')


if __name__ == '__main__':
    client.run(os.getenv('DISCORD_TOKEN'))

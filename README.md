# Calendar Bot

This is a discord bot that I implemented to manage my
[Life Calendar](https://huangweiran.club/LifeCalendar/), which is also hosted
on GitHub. Specifically, I am majorly using it to update the `<div>`s in the specific HTML 
file that records my life events, but the code can be easily modified to modify
any other file if you have a similar use case to update a file on GitHub frequently.

## How to use

1. Create a discord bot account as described [here](https://discordpy.readthedocs.io/en/latest/discord.html) and invite it to your server.
2. Create a GitHub personal access token as described [here](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token). 
Github recently provides a new functionality to [create a fine-grained access token](https://github.blog/2022-10-18-introducing-fine-grained-personal-access-tokens-for-github/),
which is recommended to use to restrict the access of the token to only the specific repository.
3. Create a `.env` file in the root directory of the project and add the following lines:
```
GITHUB_TOKEN=<your-github-token>
GITHUB_REPO_NAME=<Your-GitHub-ID>/<Your-Repo-Name>
DISCORD_TOKEN=<Your-discord-bot-token>
```
4. Make sure you have Python 3.8+ installed and run `pip install -r requirements.txt` to install the dependencies.
5. Run `python main.py` to start the bot. You can also use `nohup python main.py &` to run it in the background. Hosting it on a server is also an option.
6. Talk to the bot in your discord server. The bot will respond to the following commands:
```
!help
!new_event
!revise_event
!delete_event
!revise_event 
!delete_period 
```

An example of the `!revise_event` command is shown below:
![example](./assets/use-case.png)

With this command successfully executed, the bot will update the HTML file on GitHub and the changes will be reflected on the website:

![website](./assets/updated.png)

## How it works

The bot is implemented using the [discord.py](https://discordpy.readthedocs.io/en/latest/) library to send and receive message from the discord server, and the [PyGithub](https://pygithub.readthedocs.io/en/latest/) library to update the file on GitHub. 
[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) is used to parse the HTML file and update the `<div>`s. 
# Calendar Bot

This is a discord bot that I implemented for my own use to manage my
[Life Calendar](https://huangweiran.club/LifeCalendar/), which is also hosted
on GitHub. I am majorly using it to update the `<div>`s in the specific HTML 
file that records my life events, but the code can be easily modified to modify
any other file if you have a similar use case to update a file on GitHub frequently.

## How to use

1. Create a discord bot account as described [here](https://discordpy.readthedocs.io/en/latest/discord.html) and invite it to your server.
2. Create a GitHub personal access token as described [here](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token). 
Github recently provides a new functionally to [create a fine-grained access token](https://github.blog/2022-10-18-introducing-fine-grained-personal-access-tokens-for-github/),
which is recommended to use to restrict the access of the token to only the specific repository.
3. Create a `.env` file in the root directory of the project and add the following lines:
```
GITHUB_TOKEN=<your-github-token>
GITHUB_REPO_NAME=<Your-GitHub-ID>/<Your-Repo-Name>
DISCORD_TOKEN=<Your-discord-bot-token>
```
4. Make sure you have Python 3.8+ installed and run `pip install -r requirements.txt` to install the dependencies. (Some of the dependencies are not really used 
because the requirements.txt is auto-generated in my Conda environment, and I am too lazy to clean it up.)
5. Run `python main.py` to start the bot. You can also use `nohup python main.py &` to run it in the background. Hosting it on a server is also an option.
6. Talk to the bot in your discord server. The bot will respond to the following commands:
```
!new_event
!revise_event
!delete_event
```
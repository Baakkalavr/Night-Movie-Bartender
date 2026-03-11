# 🎬 Movie Night Bartender

Telegram bot for choosing a movie for the evening with a smart recommendation system based on IMDb ratings

## ⚠️ IMPORTANT

--

## 🚨 ANTIVIRUS

**Playwright** may trigger antivirus reactions. Playwright is a browser emulation tool needed for parsing IMDb. It can be used by both legitimate and malicious programs, but it is not a virus itself.

*Excerpt from Playwright documentation*

Some antiviruses tend to classify Playwright files as high-risk or hacking tools. The file may be deleted and quarantined.

If you encounter antivirus issues, add the project folder to exceptions, or disable PUA (Potentially Unwanted Applications) detection.

### Installation
1. Clone the repository:

> ` git clone https://github.com/bongoket/movie-night-bartender.git ` 

> ` cd movie-night-bartender `  

2. Create a virtual environment:

> ` python -m venv venv `  

> ` source venv/bin/activate `  # for Linux/Mac

> ` # venv\Scripts\activate  `  # for Windows


3. Install dependencies:

> ` pip install -r requirements.txt ` 

> ` playwright install chromium ` 

4. Create a .env file and add your bot token:

> `BOT_TOKEN=ваш_токен_от_BotFather  ` 


5. Run the bot:

> ` python -m bot.main ` 


## ℹ️ BOT COMMANDS

Command	      Description
-------------------------------------------
/start	   -   Start working with the bot
-------------------------------------------
/select	   -   Choose a movie by parameters
-------------------------------------------
/help	   -   Show help
-------------------------------------------
/cancel	   -   Cancel current action
-------------------------------------------


## MAIN MENU BUTTONS

Start - welcome and instructions

Choose movie - start selection process

My statistics - viewed movies and ratings

Top movies - best movies by IMDb rating

Help - help information

Cancel - cancel current action

## ☑️ FREQUENT QUESTIONS AND ISSUES

# Nothing happens after launching the bot

Make sure that:

- The token in .env is correct

- Antivirus is not blocking Python/Playwright

- Virtual environment (venv) is activated

# Bot doesn't find movies / says "0 available movies"

Run movie loading:

> ` python -m services.parser.movie_loader --popular 30 `  

## Telegram / Discord doesn't work after bot installation

- The bot does not affect Telegram or Discord functionality. The issue is elsewhere.

## Bot stopped working after update

IMDb structure may have changed. Try:

- Update Playwright: playwright install chromium

- Reinstall dependencies: pip install -r requirements.txt

## Antivirus complains about Playwright

- Add the project folder to antivirus exceptions.

## 🗒️ ADDING ADDITIONAL RESOURCES

The movie list for loading can be expanded by editing the file:

> ` services/parser/movie_loader.py  `  - the ` POPULAR_MOVIES  `  array
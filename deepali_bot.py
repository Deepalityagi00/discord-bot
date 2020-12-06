import os
import discord
from discord.ext import commands
from discord.ext.commands import Bot
import requests
import postgresql
from postgresql.exceptions import DuplicateTableError

Client = discord.Client()
client = commands.Bot(command_prefix = "!")
# Constants used in the File
GOOGLE_KEY = "AIzaSyDehpBD5R4UqedipYRUYxiKewc11xAu-r4"
SEARCH_ENGINE_ID = "cfb3ef7243ab90269"
QUERY_RANGE = 5
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
BOT_TOKEN = "Nzg0ODE0ODQ2NjEyNjAyOTAw.X8uxyA.iQ6qedoE2wWtbqZ5fbMB6VjSCzs ;)"

USERNAME = os.environ.get("POSTGRES_USERNAME")
PASSWORD = os.environ.get("POSTGRES_PASSWORD")
HOST = os.environ.get("POSTGRES_HOST")
PORT = "5432"
DATABASE = os.environ.get("POSTGRES_DATABASE")
# "postgres"


def perform_google_search(search_query):
    """
    Function search the <search_query> phrase on the
    google API and returns the top 5 links of pages.
    Updates the search into the database.

    :param search_query: <search phrase>
    :return: List of Links
    """
    top_links = []
    query_params = {
        "key": GOOGLE_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": search_query,
        "highRange": QUERY_RANGE,
    }
    response_data = requests.get(GOOGLE_SEARCH_URL, params=query_params)
    response_json = response_data.json()
    top_searches = response_json.get("items", [])
    top_links.extend(
        [
            f"Link: {search.get('link')} "
            for search in top_searches
            if search.get("link")
        ]
    )
    insert_data(search_query)
    return top_links


def initial_setup_db(db_connection):
    try:
        create_databse = db_connection.prepare("CREATE database deepali_bot")
        create_query = db_connection.prepare(
            "CREATE TABLE bot_history (search_history VARCHAR(255))"
        )
        with db_connection.xact():
            create_databse()
            create_query()

    except DuplicateTableError:
        return


def get_db_connection():
    """Function returns the db_connection for
    performing queries"""
    POSTGRES_URL = f"pq://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    db_connection = postgresql.open(POSTGRES_URL)
    return db_connection


def insert_data(search_query):
    """Function using for inserting the data in the mysql table"""
    db_connection = get_db_connection()
    bot_insert_query = (
        f"INSERT INTO bot_history (search_history) VALUES('{search_query}')"
    )
    try:
        bot_sql_db = db_connection.prepare(bot_insert_query)
        with db_connection.xact():
            bot_sql_db()
    except Exception:
        print("ERROR in inserting data to database")
        return

    print("Data inserted successfully")


def get_data():
    """Function using for fetching the data from table"""
    db_connection = get_db_connection()
    bot_get_query = f"SELECT search_history FROM bot_history"
    try:
        bot_db_sql = db_connection.prepare(bot_get_query)
        with db_connection.xact():
            recent_search = []
            recent_search.extend(
                [row.get("search_history") for row in bot_db_sql()]
            )  # fetch (and discard) remaining rows
    except Exception:
        print("Error in fetching the data from database")
        recent_search = []

    # Returning Unique searches
    return set(recent_search)


@client.event
async def on_ready():
    print(f"Logged in server {client}")
    db_connection = get_db_connection()
    initial_setup_db(db_connection)
    print(f"DB setup done for -> {client}")


@client.event
async def on_message(message):
    print(message.content)
    if message.author == client.user:
        return
    if message.content.startswith("hey"):
        await message.channel.send("hi")
    if message.content.startswith("!google"):
        search_query = message.content.replace("!google ", "")
        top_links = perform_google_search(search_query)
        await message.channel.send(top_links)
    if message.content.startswith("!recent game"):
        bot_searches = get_data()
        print("It returns ", bot_searches)
        await message.channel.send(bot_searches)

print("BOT Token", BOT_TOKEN)
client.run(BOT_TOKEN, bot=True)

import os
import json
from channel import Channel
from helpers import format_date_string
from datetime import datetime

from flask import Flask, session, request, render_template, jsonify
from flask_socketio import SocketIO, emit
from flask_session import Session

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"

socketio = SocketIO(app)
Session(app)

# store the users and channels from each session, starting with default "welcome"
channels = [Channel(visible_name="Welcome", cleaned_name="Welcome")]
users = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/messages", methods=["POST"])
def get_messages():

    try:
        channel_name = request.values.get('channelName')
        channel_index = get_index_of_channel_stored(channel_name)

        if channel_index is not None:
            channel_object = channels[channel_index]
            list_messages = channel_object.get_messages()
            print(f"Got messages for {channel_object.name}: {list_messages}")
        else:
            # handle weird case where local storage may still hold channel,
            # but it's not in the restarted server
            list_messages = None

        result = {
            "success": True,
            "messages": list_messages
        }
        return jsonify(result)

    except Exception as e:
        result = {
            "success": False
        }
        return jsonify(result)


@app.route("/api/create_user", methods=["POST"])
def check_username_available():

    prospective_username = request.form.get('username')

    if prospective_username not in users:
        users.append(prospective_username)
        return jsonify(available=True)
    else:
        return jsonify(available=False)


@app.route("/api/available_channels", methods=["POST"])
def available_channels():

    channel_names = [channel.name for channel in channels]

    print(f"Here is the list of available channels: {channel_names}")
    return jsonify(availableChannels=channel_names)


@socketio.on("new channel")
def add_channel(data):

    channels.append(
        Channel(
            visible_name=data['channelName'],
            cleaned_name=data['cleanedChannelName']
        )
    )

    content = {
        "new_channel": data['channelName']
    }

    print(f"Added a new channel: {data['channelName']}")
    emit("announce channel", json.dumps(content), broadcast=True)


@socketio.on("add channel user")
def new_channel_user(data):

    add_user_to_channel(data['username'], data['channelName'])

    content = {
        "channelName": data['channelName'],
        "cleanedChannelName": data['cleanedChannelName'],
        "username": data['username']
    }

    print(f"Added new user ({data['username']}) to channel ({data['channelName']})")
    emit("new channel user", json.dumps(content), broadcast=True)


@socketio.on("handle message")
def handle_message(data):

    # get the channel object from the list of channels
    channel_name = data['channelName']
    cleaned_channel_name = data['cleanedChannelName']
    channel_index = get_index_of_channel_stored(channel_name)

    # if channel index doesn't yet exist, create the object to get the index
    if channel_index is None:
        channels.append(
            Channel(
                visible_name=channel_name,
                cleaned_name=cleaned_channel_name
            )
        )
        print(f"While handling message, added this channel: {channel_name}")
        channel_index = len(channels) - 1  # order of elements in list persists

    channel_object = channels[channel_index]

    # add the message to the channel_object
    channel_object.add_message(
        user=data['user'],
        time=format_date_string(data['time']),
        content=data['message'],
        type="message"
    )

    # reset channel object at location
    channels[channel_index] = channel_object

    message_content = {
        "channelName": channel_name,
        "cleanedChannelName": cleaned_channel_name,
        "user": data['user'],
        "message_header":  data['user'] + " (" + format_date_string(data['time']) + "):",
        "message": data['message']
    }

    print(f"Adding this a message to {channel_object.name}: {message_content}")
    emit("new message", json.dumps(message_content), broadcast=True)


def add_user_to_channel(username, channel_name):

    channel_index = get_index_of_channel_stored(channel_name)
    channel_object = channels[channel_index]

    channel_object.add_user(username)
    channel_object.add_message(
        user=username,
        time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        content=f'{username} was added to channel.',
        type="announcement"
    )
    channels[channel_index] = channel_object


def get_index_of_channel_stored(channel_name):

    index_channel = 0
    for channel in channels:
        if channel.name == channel_name:
            return index_channel
        else:
            index_channel += 1
    return None

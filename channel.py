"""
Defines Channel() helper class.
"""
from message import Message
from datetime import datetime
import json


class Channel:

    def __init__(self, visible_name, cleaned_name):
        self.name = visible_name
        self.cleaned_name = cleaned_name
        self.messages = list()
        self.users = list()
        self.date_created = datetime.now()

    def add_message(self, user, time, content, message_type):
        """
        Adds a new message object to the list of Messages in this channel. Channel can only hold
        100 messages at a time; older messages will be removed.

        :param user: username of person who submitted the message
        :param time: time that the message was submitted by user
        :param content: text of the message
        """
        self.messages.append(
            Message(
                user=user,
                time_created=time,
                content=content,
                message_type=message_type
            )
        )

        for message in self.messages:
            print(message)

        # once 100 messages is met, pop the oldest message off
        if len(self.messages) > 100:
            self.messages.pop(0)

    def add_user(self, user):
        """
        Add a new user to the channel
        :param user: username of new user
        """
        self.users.append(user)

    def get_messages(self):
        """
        Formats all stored messages and their content as a list of dictionary objects
        and returns a json string.

        :return: json string containing list of messages
        """

        list_messages = [
            {
                "channelName": self.name,
                "cleanedChannelName": self.cleaned_name,
                "user": message.user,
                "message_header": message.user + " (" + message.time_created + "):",
                "message": message.content,
                "type": message.message_type
            } for message in self.messages
        ]

        dict_messages = {
            "channel": self.name,
            "messages": list_messages
        }

        return json.dumps(dict_messages)

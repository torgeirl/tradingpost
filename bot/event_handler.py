import json
import logging
from re import search

logger = logging.getLogger(__name__)


class RtmEventHandler(object):
    def __init__(self, slack_clients, msg_writer):
        self.clients = slack_clients
        self.msg_writer = msg_writer

    def handle(self, event):
        if 'type' in event:
            self._handle_by_type(event['type'], event)

    def _handle_by_type(self, event_type, event):
        # see https://api.slack.com/rtm for a full list of events
        if event_type == 'error':
            # error
            self.msg_writer.write_error(event['channel'], json.dumps(event))
        elif event_type == 'message':
            # message was sent to channel
            self._handle_message(event)
        elif event_type == 'channel_joined':
            # you joined a channel
            self.msg_writer.write_help_message(event['channel'])
        elif event_type == 'group_joined':
            # you joined a private group
            self.msg_writer.write_help_message(event['channel'])
        else:
            pass

    def _handle_message(self, event):
        # filter out messages from the bot itself, and from non-users (eg. webhooks)
        if ('user' in event) and (not self.clients.is_message_from_me(event['user'])):

            msg_txt = event['text'].lower()

            if self.clients.is_bot_mention(event['text']):
                # e.g. user typed: "@pybot tell me a joke!"
                if search('help', msg_txt):
                    self.msg_writer.write_help_message(event['channel'])
                elif search('joke', msg_txt):
                    self.msg_writer.write_joke(event['channel'])
                elif search('hi|hey|hello|howdy', msg_txt):
                    self.msg_writer.write_greeting(event['channel'], event['user'])
                else:
                    self.msg_writer.write_prompt(event['channel'])
            elif search('!card|!oracle|!price|!pwp', msg_txt):
                if msg_txt.startswith('!card '):
                    self.msg_writer.write_card(event['channel'], msg_txt[5:].strip())
                elif msg_txt.startswith('!oracle '):
                    self.msg_writer.write_oracle(event['channel'], msg_txt[7:].strip())
                elif msg_txt.startswith('!price '):
                    self.msg_writer.write_price(event['channel'], msg_txt[6:].strip())
                elif msg_txt.startswith('!pwp '):
                    self.msg_writer.write_pwp(event['channel'], msg_txt[4:].strip())
            else:
                pass

# -*- coding: utf-8 -*-

import logging
import json
import random
import re
import requests

logger = logging.getLogger(__name__)


def find_index_of_sequence(data, sequence, start_index=0):
    index = start_index
    for token in sequence:
        index = data.find(token, index)
        if index == -1:
            return -1
    return index + len(sequence[-1])


def emoji_filter(input):
    ret = input.replace('{', ':_')
    ret = ret.replace('}', '_:')
    lastpos = None
    while ret.rfind('_:', 0, lastpos) != -1:
        end = ret.rfind('_:', 0, lastpos)
        lastpos = ret.rfind(':_', 0, lastpos)
        start = lastpos + 2
        content = ret[start:end]
        content = content.lower()
        content = content.replace('/', '')
        ret = ret[:start] + content + ret[end:]
    return ret


def get_card_value(card_name, set_code):
    url = 'http://www.mtggoldfish.com/widgets/autocard/%s [%s]' % (card_name, set_code)
    headers = {
        'Pragma': 'no-cache',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8,de;q=0.6,sv;q=0.4',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36',
        'Accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01',
        'Referer': 'http://www.mtggoldfish.com/widgets/autocard/%s' % card_name,
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }
    response = requests.get(url, headers=headers)
    index = find_index_of_sequence(response.content, ['tcgplayer', 'btn-shop-price', '$'])
    end_index = response.content.find('\\n', index)
    try:
        value = float(response.content[index + 2:end_index].replace(',', ''))
    except ValueError:
        value = 0
    return value


def get_card(name):
    query_url = 'http://api.deckbrew.com/mtg/cards?name=%s' % name
    r = requests.get(query_url)
    try:
        cards = r.json()
    except ValueError:
        logging.error(u'No JSON object could be decoded from API response: %s' % r)
        return None

    if len(cards) < 1:
        return None

    card = None
    for element in cards:
        if element['name'].lower() == name.lower():
            card = element
    return card


def get_seasons(dci_number):
    '''Returns to current and last season for that DCI number'''
    url = 'http://www.wizards.com/Magic/PlaneswalkerPoints/JavaScript/GetPointsHistoryModal'
    headers = {
        'Pragma': 'no-cache',
        'Origin': 'http://www.wizards.com',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.8,de;q=0.6,sv;q=0.4',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': '*/*',
        'Cache-Control': 'no-cache',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': 'f5_cspm=1234; BIGipServerWWWPWPPOOL01=353569034.20480.0000; __utmt=1; BIGipServerWWWPool1=3792701706.20480.0000; PlaneswalkerPointsSettings=0=0&lastviewed=9212399887; __utma=75931667.1475261136.1456488297.1456488297.1456488297.1; __utmb=75931667.5.10.1456488297; __utmc=75931667; __utmz=75931667.1456488297.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
        'Connection': 'keep-alive',
        'Referer': 'http://www.wizards.com/Magic/PlaneswalkerPoints/%s' % dci_number
    }
    data = {'Parameters': {'DCINumber': dci_number, 'SelectedType': 'Yearly'}}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code is 200:
        seasons = []

        try:
            response_data = json.loads(response.content)
            markup = response_data['ModalContent']
            search_position = markup.find('SeasonRange')

            while search_position != -1:
                pointsvalue = 'PointsValue\">'
                search_position = markup.find(pointsvalue, search_position)
                search_position += len(pointsvalue)
                end_position = markup.find('</div>', search_position)
                if end_position != -1:
                    value = markup[search_position:end_position]
                    seasons.append(int(value))
                search_position = markup.find('SeasonRange', search_position)
        except ValueError:
            logging.error(u'No JSON object could be decoded from API response: %s' % response)
            return 'Garbled response from backend. Please try again later.'

        try:
            return {'currentSeason': seasons[0], 'lastSeason': seasons[1]}
        except IndexError:
            return 'DCI# %s not found.' % dci_number
    else:
        logging.error(u'No response from API (HTTP code %i)' % response.status_code)
        return 'No response from backend. Please try again later.'


class Messenger(object):
    def __init__(self, slack_clients):
        self.clients = slack_clients


    def send_message(self, channel_id, msg):
        # in the case of Group and Private channels, RTM channel payload is a complex dictionary
        if isinstance(channel_id, dict):
            channel_id = channel_id['id']
        logger.debug('Sending msg: %s to channel: %s' % (msg, channel_id))
        channel = self.clients.rtm.server.channels.find(channel_id)
        channel.send_message(msg)


    def write_help_message(self, channel_id):
        bot_uid = self.clients.bot_user_id()
        txt = '{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}'.format(
            'I\'m your friendly Slack bot written in Python.  I\'ll *_respond_* to the following commands:',
            '> `hi <@' + bot_uid + '>` - I\'ll respond with a randomized greeting mentioning your username. :wave:',
            '> `<@' + bot_uid + '> joke` - I\'ll tell you one of my finest jokes, with a typing pause for effect. :laughing:',
            '> `<@' + bot_uid + '> help` - I\'ll reply with this helpful text. :information_source:',
            '> `!card cardname` - I\'ll post a picture of the named card. :frame_with_picture:',
            '> `!price cardname` - I\'ll respond with the card\'s current market price. :moneybag:',
            '> `!oracle cardname` - I\'ll respond with the card\'s oracle text. :book:',
            '> `!pwp dcinumber` - I\'ll tell you a player\'s PWP score and bye eligibility. :trophy:')
        self.send_message(channel_id, txt)


    def write_greeting(self, channel_id, user_id):
        greetings = ['Hi', 'Hello', 'Nice to meet you', 'Howdy', 'Salutations']
        txt = '{}, <@{}>!'.format(random.choice(greetings), user_id)
        self.send_message(channel_id, txt)


    def write_prompt(self, channel_id):
        bot_uid = self.clients.bot_user_id()
        txt = 'I\'m sorry, I didn\'t quite understand... Can I help you? (e.g. `<@' + bot_uid + '> help`)'
        self.send_message(channel_id, txt)


    def write_joke(self, channel_id):
        with open('/src/bot/jokes.json', 'r') as infile:
            joke = random.choice(json.load(infile))
        self.send_message(channel_id, joke['setup'])
        self.clients.send_user_typing_pause(channel_id)
        self.send_message(channel_id, joke['punchline'])


    def write_error(self, channel_id, err_msg):
        txt = ':face_with_head_bandage: my maker didn\'t handle this error very well:\n>```{}```'.format(err_msg)
        self.send_message(channel_id, txt)


    def write_card(self, channel_id, search_term):
        card = get_card(search_term)

        if card:
            most_recent_printing = card['editions'][0]
            txt = ''
            attachment = {
                'title': card['name'].replace('\'', '\\\''),
                'image_url': most_recent_printing['image_url'],
                'footer': '%s (%s)' % (most_recent_printing['set'], most_recent_printing['set_id']),
            }
            self.clients.web.chat.post_message(channel_id, txt, attachments=[attachment], as_user='true')
        else:
            txt = 'Card not found.'
            self.send_message(channel_id, txt)


    def write_oracle(self, channel_id, search_term):
        card = get_card(search_term)

        if card:
            typeline = ''
            if 'supertypes' in card:
                for supertype in card['supertypes']:
                    typeline += supertype.capitalize() + ' '
            if 'types' in card:
                for cardtype in card['types']:
                    typeline += cardtype.capitalize() + ' '
                if 'subtypes' in card:
                    typeline += '- '
            if 'subtypes' in card:
                for subtype in card['subtypes']:
                    typeline += subtype.capitalize() + ' '
            txt = u'*%s %s*\n%s\n%s' % (card['name'], card['cost'], typeline, card['text'])
            if 'power' in card and 'toughness' in card:
                txt += u'\n*`%s/%s`*' % (card['power'], card['toughness'])
            if 'loyalty' in card:
                txt += u'\n*`%s`*' % card['loyalty']
            txt = emoji_filter(txt)
        else:
            txt = 'Card not found.'
        self.send_message(channel_id, txt)


    def write_price(self, channel_id, search_term):
        card = get_card(search_term)

        if card:
            most_recent_printing = card['editions'][0]
            card['value'] = get_card_value(card['name'], most_recent_printing['set_id'])
            txt = 'Unable to find price information for %s' % card['name']
            if card['value'] > 0:
                txt = ('Current market price for most recent printing of %s (%s) - $%.1f' %
                       (card['name'], most_recent_printing['set'], card['value']))
        else:
            txt = 'Card not found.'
        self.send_message(channel_id, txt)


    def write_pwp(self, channel_id, dci_number):
        if dci_number.isdigit():
            response = get_seasons(dci_number)

            if isinstance(response, dict):
                txt = ('DCI# %s has %s points in the current season, and %s points last season.\nCurrently '
                       % (dci_number, response['currentSeason'], response['lastSeason']))

                if response['currentSeason'] >= 2250 or response['lastSeason'] >= 2250:
                    txt += 'eligible for 2 GP byes.'
                elif response['currentSeason'] >= 1300 or response['lastSeason'] >= 1300:
                    txt += 'eligible for 1 GP bye.'
                else:
                    txt += 'not eligible for GP byes.'
            else:
                txt = response
        else:
            txt = '\'%s\' doesn\'t look like a DCI number. Try again, but with an actual number.' % dci_number
        self.send_message(channel_id, txt)

    def write_roll(self, channel_id, sides):
        if sides == '':
            sides = 6

        try:
            sides = int(sides)
        except ValueError:
            self.send_message('Please supply a valid number of sides.')
            return

        intro = 'Rolled a {}-sided die, and the results is...'
        result = '{}! :game_die: :game_die:'.format(random.randint(1, sides))

        self.send_message(channel_id, intro.format(sides))
        self.clients.send_user_typing_pause(channel_id)
        self.send_message(channel_id, result)


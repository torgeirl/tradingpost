import logging
import json
import random
import requests

logger = logging.getLogger(__name__)


def findIndexOfSequence(data, sequence, startIndex=0):
    index = startIndex
    for token in sequence:
        index = data.find(token, index)
        if index == -1:
            return -1
    return index + len(sequence[-1])


def getCardValue(cardName, setCode):
    url = "http://www.mtggoldfish.com/widgets/autocard/%s [%s]" % (cardName, setCode)
    headers = {
        'Pragma': 'no-cache',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8,de;q=0.6,sv;q=0.4',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36',
        'Accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01',
        'Referer': 'http://www.mtggoldfish.com/widgets/autocard/%s' % cardName,
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }
    response = requests.get(url, headers=headers)
    index = findIndexOfSequence(response.content, ["tcgplayer", "btn-shop-price", "$"])
    endIndex = response.content.find("\\n", index)
    try:
        value = float(response.content[index + 2:endIndex].replace(",", ""))
    except ValueError:
        value = 0

    return value


def getCard(name):
    queryUrl = "http://api.deckbrew.com/mtg/cards?name=%s" % name
    print queryUrl
    r = requests.get(queryUrl)
    cards = r.json()

    if len(cards) < 1:
        return None

    card = cards[0]
    bestMatch = None
    for cardIter in cards:
        pos = cardIter["name"].lower().find(name)
        if bestMatch is None or (pos != -1 and pos < bestMatch):
            bestMatch = pos
            card = cardIter

    mostRecent = card["editions"][0]
    card["value"] = getCardValue(card["name"], mostRecent["set_id"])
    return card


def getSeasons(dciNumber):
    url = "http://www.wizards.com/Magic/PlaneswalkerPoints/JavaScript/GetPointsHistoryModal"
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
        'Referer': 'http://www.wizards.com/Magic/PlaneswalkerPoints/%s' % dciNumber
    }
    data = {"Parameters": {"DCINumber": dciNumber, "SelectedType": "Yearly"}}
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code is 200:
        seasons = []

        responseData = json.loads(response.content)
        markup = responseData["ModalContent"]
        searchPosition = markup.find("SeasonRange")

        while searchPosition != -1:
            pointsvalue = "PointsValue\">"
            searchPosition = markup.find(pointsvalue, searchPosition)
            searchPosition += len(pointsvalue)
            endPosition = markup.find("</div>", searchPosition)
            if endPosition != -1:
                value = markup[searchPosition:endPosition]
                seasons.append(int(value))
            searchPosition = markup.find("SeasonRange", searchPosition)

        return {"currentSeason": seasons[0], "lastSeason": seasons[1]}
    else:
        return None


class Messenger(object):
    def __init__(self, slack_clients):
        self.clients = slack_clients

    def send_message(self, channel_id, msg):
        # in the case of Group and Private channels, RTM channel payload is a complex dictionary
        if isinstance(channel_id, dict):
            channel_id = channel_id['id']
        logger.debug('Sending msg: {} to channel: {}'.format(msg, channel_id))
        channel = self.clients.rtm.server.channels.find(channel_id)
        channel.send_message("{}".format(msg.encode('ascii', 'ignore')))

    def write_help_message(self, channel_id):
        bot_uid = self.clients.bot_user_id()
        txt = '{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}'.format(
            "I'm your friendly Slack bot written in Python.  I'll *_respond_* to the following commands:",
            "> `hi <@" + bot_uid + ">` - I'll respond with a randomized greeting mentioning your username. :wave:",
            "> `<@" + bot_uid + "> joke` - I'll tell you one of my finest jokes, with a typing pause for effect. :laughing:",
            "> `<@" + bot_uid + "> help` - I'll reply with this helpful text. :information_source:",
            "> `!card cardname` - I'll post a picture of the named card. :frame_with_picture:",
            "> `!price cardname` - I'll respond with the card's current market price. :moneybag:",
            "> `!oracle cardname` - I'll respond with the card's oracle text. :book:",
            "> `!pwp dcinumber` - I'll tell you a player's PWP score and bye eligibility. :trophy:")
        self.send_message(channel_id, txt)

    def write_greeting(self, channel_id, user_id):
        greetings = ['Hi', 'Hello', 'Nice to meet you', 'Howdy', 'Salutations']
        txt = '{}, <@{}>!'.format(random.choice(greetings), user_id)
        self.send_message(channel_id, txt)

    def write_prompt(self, channel_id):
        bot_uid = self.clients.bot_user_id()
        txt = "I'm sorry, I didn't quite understand... Can I help you? (e.g. `<@" + bot_uid + "> help`)"
        self.send_message(channel_id, txt)

    def write_joke(self, channel_id):
        with open('/src/bot/jokes.json', 'r') as infile:
            joke = random.choice(json.load(infile))
        self.send_message(channel_id, joke["setup"])
        self.clients.send_user_typing_pause(channel_id)
        self.send_message(channel_id, joke["punchline"])

    def write_error(self, channel_id, err_msg):
        txt = ":face_with_head_bandage: my maker didn't handle this error very well:\n>```{}```".format(err_msg)
        self.send_message(channel_id, txt)

    def write_card(self, channel_id, searchTerm):
        card = getCard(searchTerm)

        if card:
            mostRecentPrinting = card["editions"][0]
            txt = ""
            attachment = {
                "title": card["name"].replace("\"", "\\\""),
                "image_url": mostRecentPrinting["image_url"],
                "footer": "%s (%s)" % (mostRecentPrinting["set"], mostRecentPrinting["set_id"]),
            }
            self.clients.web.chat.post_message(channel_id, txt, attachments=[attachment], as_user='true')
        else:
            txt = 'Card not found.'
            self.send_message(channel_id, txt)

    def write_oracle(self, channel_id, searchTerm):
        card = getCard(searchTerm)

        if card:
            typeline = ""
            if "supertypes" in card:
                for supertype in card["supertypes"]:
                    typeline += supertype.capitalize() + " "
            if "types" in card:
                for cardtype in card["types"]:
                    typeline += cardtype.capitalize() + " "
                if "subtypes" in card:
                    typeline += "- "
            if "subtypes" in card:
                for subtype in card["subtypes"]:
                    typeline += subtype.capitalize() + " "
            txt = "*%s %s*\n%s\n%s" % (card["name"], card["cost"], typeline, card["text"].replace(u'\u2212', '-'))
            if "power" in card and "toughness" in card:
                txt += "\n*`%s/%s`*" % (card["power"], card["toughness"])
            if "loyalty" in card:
                txt += "\n*`%s`*" % card["loyalty"]
        else:
            txt = 'Card not found.'
        self.send_message(channel_id, txt)

    def write_price(self, channel_id, searchTerm):
        card = getCard(searchTerm)

        if card:
            mostRecentPrinting = card["editions"][0]
            txt = "Unable to find price information for %s" % card["name"]
            if card["value"] > 0:
                txt = ("Current market price for most recent printing of %s (%s) - $%.1f" %
                       (card["name"], mostRecentPrinting["set"], card["value"]))
        else:
            txt = 'Card not found.'
        self.send_message(channel_id, txt)

    def write_pwp(self, channel_id, dciNumber):
        planeswalker = getSeasons(dciNumber)

        if planeswalker:
            txt = ("DCI# %s has %s points in the current season, and %s points last season.\nCurrently "
                   % (dciNumber, planeswalker["currentSeason"], planeswalker["lastSeason"]))

            if planeswalker["currentSeason"] >= 2250 or planeswalker["lastSeason"] >= 2250:
                txt += "eligible for 2 GP byes."
            elif planeswalker["currentSeason"] >= 1300 or planeswalker["lastSeason"] >= 1300:
                txt += "eligible for 1 GP bye."
            else:
                txt += "not eligible for GP byes."
        else:
            txt = "DCI# %s not found." % dciNumber
        self.send_message(channel_id, txt)

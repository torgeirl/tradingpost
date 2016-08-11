import logging
import random

logger = logging.getLogger(__name__)


def getPlaneswalker(dciNumber):
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
    data = {"Parameters":{"DCINumber":dciNumber,"SelectedType":"Yearly"}}
    response = requests.post(url, headers=headers, data=json.dumps(data))

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

def getPlaneswalkerByes(player):
    if player["currentSeason"] >= 2250 or player["lastSeason"] >= 2250:
        return 2
    elif player["currentSeason"] >= 1300 or player["lastSeason"] >= 1300:
        return 1

    return 0

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
        txt = '{}\n{}\n{}\n{}'.format(
            "I'm your friendly Slack bot written in Python.  I'll *_respond_* to the following commands:",
            "> `hi <@" + bot_uid + ">` - I'll respond with a randomized greeting mentioning your user. :wave:",
            "> `<@" + bot_uid + "> joke` - I'll tell you one of my finest jokes, with a typing pause for effect. :laughing:",
            "> `<@" + bot_uid + "> attachment` - I'll demo a post with an attachment using the Web API. :paperclip:")
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
        question = "Why did the python cross the road?"
        self.send_message(channel_id, question)
        self.clients.send_user_typing_pause(channel_id)
        answer = "To eat the chicken on the other side! :laughing:"
        self.send_message(channel_id, answer)

    def write_error(self, channel_id, err_msg):
        txt = ":face_with_head_bandage: my maker didn't handle this error very well:\n>```{}```".format(err_msg)
        self.send_message(channel_id, txt)

    def write_card(self, channel_id, msg_txt):
        txt = ''
        self.send_message(channel_id, txt)
        #TODO

    def write_oracle(self, channel_id, msg_txt):
        txt = ''
        self.send_message(channel_id, txt)
        #TODO

    def write_price(self, channel_id, msg_txt):
        txt = ''
        self.send_message(channel_id, txt)
        #TODO

    def write_pwp(self, channel_id, dcinr):
	planeswalker = getPlaneswalker(dcinr)
        if planeswalker > -1:
	        txt = "DCI# %s has %s point(s) in the current season, %s point(s) last season.\nCurrently " % (dcinr, planeswalker["currentSeason"], planeswalker["lastSeason"])
	        byes = getPlaneswalkerByes(planeswalker)
	        if not byes:
		        txt += "not eligible for GP byes."
	        else:
		        txt += "eligible for %d GP bye(s)." % byes
        else:
                txt = "DCI# %s not found." % dcinr
        self.send_message(channel_id, txt)


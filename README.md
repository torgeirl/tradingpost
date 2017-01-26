tradingpost-beepboop
=============

## Overview
A simple Magic: the Gathering bot, implemented to be a Beep Boop hostable, Python-based Slack bot.

## Assumptions
* You have already signed up with Beep Boop and have a local fork of this project.
* You have sufficient rights in your Slack team to configure a bot and generate/access a Slack API token.

## Usage

### Run locally
Install dependencies ([virtualenv](http://virtualenv.readthedocs.org/en/latest/) is recommended.)

	pip install -r requirements.txt
	export SLACK_TOKEN=<YOUR SLACK TOKEN>; python ./bot/app.py

Things are looking good if the console prints something like:

	Connected <your bot name> to <your slack team> team at https://<your slack team>.slack.com.

If you want change the logging level, prepend `export LOG_LEVEL=<your level>; ` to the `python ./bot/app.py` command.

### Run locally in Docker
	docker build -t starter-python-bot .
	docker run --rm -it -e SLACK_TOKEN=<YOUR SLACK API TOKEN> starter-python-bot

### Run in BeepBoop
If you have linked your local repo with the Beep Boop service (check [here](https://beepboophq.com/0_o/my-projects)), changes pushed to the remote master branch will automatically deploy.


## Credits
I got the inspiration to make Tradingpost after seeing Filip Söderholm's [cardfetcher bot](https://github.com/fiso/cardfetcher) in action, and I have re-used part of his code while making Tradingpost.

The [BeepBoop](https://beepboophq.com/docs/article/overview) bot design of this project is heavily inspired by [BeepBoopHQ's Starter Python bot](https://github.com/BeepBoopHQ/starter-python-bot/) (MIT license).

## License
See the [LICENSE](LICENSE.md) file for license rights and limitations (MIT).

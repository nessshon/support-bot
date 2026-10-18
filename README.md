# 🤖 Support Bot

[![License](https://img.shields.io/github/license/nessshon/support-bot)](https://github.com/nessshon/support-bot/blob/main/LICENSE)
[![Telegram Bot](https://img.shields.io/badge/Bot-grey?logo=telegram)](https://core.telegram.org/bots)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Redis](https://img.shields.io/badge/Redis-Yes?logo=redis&color=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-blue?logo=docker&logoColor=white)](https://www.docker.com/)

**Support Bot** is a Telegram bot for feedback: every user who writes to the bot gets their own topic in your forum
group, and admins answer right in the topic.

* **Both ways.** Messages, edits, replies and reactions reach the other side; forwards keep their source.
* **Delivery.** Undelivered messages are queued and sent later, in order; albums stay albums.
* **Control.** Block a user, turn on silent mode for a topic, see the user's details. New users pass a captcha.
* **Languages.** A file per language in [locales](https://github.com/nessshon/support-bot/tree/main/locales); users pick theirs, the group has its own.

* Bot example: [@nessshonSupportBot](https://t.me/nessshonSupportBot)
* Linked group example: [@nessshonSupportGroup](https://t.me/nessshonSupportGroup)

**About Limits**:
<blockquote>
Specific limits are not specified in the documentation, but the community has shared some rough numbers. 
<br>
• Limit on topic creation per minute <b>~20</b>.
<br>
• Limit on the total number of topics <b>~1M</b>.
</blockquote>

### Available bot commands

In the group topics:

* `/ban` - Block / unblock the user. The user's messages stop reaching the topic.
* `/silent` - Turn silent mode on / off. Messages from the topic don't reach the user.
* `/delete` - Delete a support message for the user. Reply with it to a message up to 48 hours old.
* `/information` - User details: ID, username, language, status, block and silent mode.

In the chat with the bot:

* `/start` - Restart the bot.
* `/delete` - Delete a message. Reply with it to your own message up to 48 hours old.
* `/language` - Change the language (only with more than one language).

A message deleted by hand stays on the other side: Telegram doesn't tell bots. Use `/delete`.

## Usage

### Preparation

1. Create a bot via [@BotFather](https://t.me/BotFather) and save its token (`BOT_TOKEN`).
2. Create a group and enable topics in the group settings.
3. Add the bot to the group as an admin with the rights to manage topics, delete messages and pin messages.
4. Add [What's my Telegram ID?](https://t.me/my_id_bot) to the group and save the group ID (`BOT_GROUP_ID`).
5. Optionally, edit the bot texts in [locales](https://github.com/nessshon/support-bot/tree/main/locales).
6. Optionally, add a language: copy `en.toml` to `de.toml` (the language code) and translate it.

Every message an admin writes in the user's topic goes to the user. Messages of anonymous admins are ignored, so that
it is always clear who replied. On start the bot checks the group and stops with a clear error if the group ID is
wrong, topics are off or the bot can't manage them.

### Installation

You need your own server or you can rent one from a hosting provider. For this, check out the [Recommended Hosting Provider](#recommended-hosting-provider) section below.

1. Clone the repository:

    ```bash
    git clone https://github.com/nessshon/support-bot.git
    ```

2. Change into the bot directory:

    ```bash
    cd support-bot
    ```
3. Copy the environment variables file:

   ```bash
   cp .env.example .env
   ```

4. Configure the [environment variables](#environment-variables-reference) file:

   ```bash
   nano .env
   ```

5. Running a bot in a docker container:

   ```bash
   docker compose up -d --build
   ```

   Check that it started: `docker compose logs -f bot`.

## Environment Variables Reference

Here is a comprehensive reference guide for the environment variables used in the project:

| Variable             | Description                                                                                                 | Example               |
|----------------------|-------------------------------------------------------------------------------------------------------------|-----------------------|
| `BOT_TOKEN`          | Bot token, obtained from [@BotFather](https://t.me/BotFather)                                               | `123456:qweRTY`       |
| `BOT_DEV_ID`         | User ID of the bot developer, who gets error reports                                                        | `123456789`           |
| `BOT_GROUP_ID`       | Group ID where the bot operates                                                                             | `-100123456789`       |
| `BOT_EMOJI_ID`       | The custom emoji ID for the group's topic.                                                                  | `5417915203100613993` |
| `BOT_GROUP_LANGUAGE` | Optional. Language of everything the bot writes to the group, a file name from `locales`, `en` by default   | `ru`                  |
| `REDIS_HOST`         | The hostname or IP address of the Redis server                                                              | `redis`               |
| `REDIS_PORT`         | The port number on which the Redis server is running                                                        | `6379`                |
| `REDIS_DB`           | The Redis database number                                                                                   | `0`                   |
| `REDIS_USERNAME`     | Optional. Redis ACL username                                                                                | `default`             |
| `REDIS_PASSWORD`     | Optional. Redis password                                                                                    | `p@ss:w/rd`           |

## Recommended Hosting Provider

I recommend using [aeza.net](https://aeza.net/?ref=362599) for your hosting needs. Here's why:

- **24/7 Support**: Quick and effective support via chat or phone.
- **Promo Plan for €1.9**: Great for testing Telegram bots and small websites.
- **Easy Backups**: Secure backups on independent servers.
- **Hourly Billing**: Rent a server by the hour for testing or demos.
- **Anti-DDoS Protection**: Reliable and secure internet connection for your business.
- **Multiple Payment Methods**: Supports various payment methods, including cryptocurrencies like TON.

Learn more at [aeza.net](https://aeza.net/?ref=362599).

## Contribution

We welcome your contributions! If you have ideas for improvement or have identified a bug, please create an issue or
submit a pull request.

## License

This repository is distributed under the [MIT License](LICENSE).
Feel free to use, modify, and distribute the code in accordance with the terms of the license.

# 🤖 Support Bot

[![License](https://img.shields.io/github/license/tonmendon/ton-subdomain)](https://github.com/tonmendon/ton-subdomain/blob/main/LICENSE)
[![Telegram Bot](https://img.shields.io/badge/Bot-grey?logo=telegram)](https://core.telegram.org/bots)
[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Redis](https://img.shields.io/badge/Redis-Yes?logo=redis&color=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-blue?logo=docker&logoColor=white)](https://www.docker.com/)

**Support Bot** is a specially designed Telegram bot for feedback. With built-in support for topics, all user messages
are intelligently categorized, promoting organized and streamlined discussion in your group. It provides features such
as blocking unwanted users, silent mode in topics for discreet conversations, and more. Improve group communication with
Support Bot!

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

<details>
<summary><b>Available bot commands in the group topics</b></summary>

* `/ban` - Block/Unblock User.

  Use this command to block or unblock a user, controlling the receipt of messages from them.

* `/silent` - Activate/Deactivate Silent Mode.

  Enable or disable silent mode to prevent messages from being sent to the user.

* `/information` - User Information.

  Receive a message containing basic information about the user.

</details>

## Usage

<details>
<summary><b>Preparation</b></summary>

1. Create a bot via [@BotFather](https://t.me/BotFather) and save the TOKEN (referred to as `BOT_TOKEN` later).
2. Create a group and enable topics in the group settings.
3. Add the created bot to the group as an admin and grant it the necessary rights to manage topics.
4. Add the bot [What's my Telegram ID?](https://t.me/my_id_bot) to the group and save the group ID (referred to
   as `BOT_GROUP_ID` later).
5. Optionally, customize the bot texts to fit your needs in the file
   named [texts](https://github.com/nessshon/support-bot/tree/main/app/bot/utils/texts.py).
6. Optionally, add the language you need
   to [SUPPORTED_LANGUAGES](https://github.com/nessshon/support-bot/tree/main/app/bot/utils/texts.py#L4)
   and add the appropriate codes to
   the [data](https://github.com/nessshon/support-bot/tree/main/app/bot/utils/texts.py#L49).

</details>

<details>
<summary><b>Installation</b></summary>

1. Clone the repository:

    ```bash
    git clone https://github.com/nessshon/support-bot.git
    ```

2. Change into the bot directory:

    ```bash
    cd support-bot
    ```
3. Clone environment variables file:

   ```bash
   cp .env.example .env
   ```

4. Configure [environment variables](#environment-variables-reference) variables file:

   ```bash
   nano .env
   ```

5. Running a bot in a docker container:

   ```bash
   docker-compose up --build
   ```

</details>

## Environment Variables Reference

<details>
<summary>Click to expand</summary>

Here is a comprehensive reference guide for the environment variables used in the project:

| Variable       | Type  | Description                                                   | Example         |
|----------------|-------|---------------------------------------------------------------|-----------------|
| `BOT_TOKEN`    | `str` | Bot token, obtained from [@BotFather](https://t.me/BotFather) | `123456:qweRTY` | 
| `BOT_DEV_ID`   | `int` | User ID of the bot developer or admin                         | `123456789`     |
| `BOT_GROUP_ID` | `str` | Group ID where the bot operates                               | `-100123456789` |
| `REDIS_HOST`   | `str` | The hostname or IP address of the Redis server                | `redis`         |
| `REDIS_PORT`   | `int` | The port number on which the Redis server is running          | `6379`          |
| `REDIS_DB`     | `int` | The Redis database number                                     | `1`             |

</details>

## Contribution

We welcome your contributions! If you have ideas for improvement or have identified a bug, please create an issue or
submit a pull request.

## Donations

**TON** - `EQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNess`

**USDT** (TRC-20) - `TJjADKFT2i7jqNJAxkgeRm5o9uarcoLUeR`

## License

This repository is distributed under the [MIT License](LICENSE).
Feel free to use, modify, and distribute the code in accordance with the terms of the license.

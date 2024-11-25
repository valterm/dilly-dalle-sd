
# Dilly Dalle - Stable Diffusion

A telegram bot integrating with the [AUTOMATIC1111 stable diffusion interface](https://github.com/AUTOMATIC1111/stable-diffusion-webui) to bring genAI images directly to your chats.

## Supported Commands
|Command|Parameters|Function|
|--|--|--|
|/picgen|prompt|Generate a new image based on the prompt|
|/variation|an image + a text prompt|Generate a variation of the supplied image|
|/variation|replied to an image + a text prompt | Generate a variation of the supplied image|
|/safemode|on\|off|Turn spoiler filtered images on or off|
|/teach|%keyword replacement text|Teach a word that you can substitue in prompts using the % sign as a marker|
|/forget|%keyword|Frogets the taught keyword|
|/mywords||Display all your known words|

## Notes
* The bot works based on user + chat combinations. On first image generation, the user and chat combination will be logged into a table in the database, and will be used for the custom commands
* Safemode status and words are user+chat specific
* The user/chat combination is only logged on image generation; safemode and aliasing will not work until at least one image has been generated

## Installation
Stable Diffusion is not part of the package; you will need to first set up the SD Web UI, and launch it in API mode (--noui).
Once you have it set, create a telegram bot using [@BotFather](https://telegram.me/BotFather). You can set all details as you like, the bot is 100% in your control.

Set the bot commands to these:
```
start - Start the bot
picgen - Create new image from prompt
variation - Create a variation from the image
teach - Teach aliases to be replaced in the prompts
forget - Forget a learned alias
mywords - Get a list of all your aliases
safemode - Toggle spoiler filter mode
```

Grab your bot token, and bot username. and paste them into the `docker-compose.yml` env variables:

```yaml
version: "3.9"
services:
  dilly-dalle-sd:
    container_name: "dilly-dalle-sd-bot"
    build: .
    restart: always
    environment:
    - "LOGLEVEL=ERROR" # DEBUG, INFO, WARNING, ERROR, CRITICAL
    - "TELEGRAM_BOT_TOKEN="
    - "STABLE_DIFFUSION_URL="
    - "DATABASE_URL=/app/data/sqlite/dilly-dalle-sd.db" # Only modify if you want different volume mappings. If you change the filename update entrypoint.sh
    - "STEPS=20" # The number of steps when creating the image
    volumes:
      - ./data:/app/data # sqlite db and generated images
```

Make sure to adjust the `STABLE_DIFFUSION_URL` to point to your host address if you're running SD on a different machine.

Afterwards, start the container with:
```bash
docker compose up -d
```

This will build the image and start a container.
The generated images and the back-end sqlite database will be stored in the `data` directory created when starting.


## License
This code is being released under CC BY-NC-SA 4.0. 
See the `LICENSE` file for details.

Additionally, the following third party libraries are used, without modification:

|Library|Version|License|
|--|--|--|
|[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) |21.2|GNU Lesser General Public License v3.0|
|[requests](https://github.com/psf/requests)|2.31.0|Apache License 2.0|
|[Pillow](https://github.com/python-pillow/Pillow/tree/main)|10.2.0|Historical Permission Notice and Disclaimer (HPND)|
|[apsw](https://github.com/rogerbinns/apsw/tree/master)|3.45.1.0|Open Source License|


General Notices
This software dynamically links to libraries that are licensed under licenses differing from CC BY-NC-SA 4.0. Users are informed of their rights under this license and can obtain the source code of these libraries from the respective repositories linked above.

## Support
Please use the github issues page to report bugs and problems.

If you want to contribute, feel free to [buy me a coffee.](https://paypal.me/mevalter/)

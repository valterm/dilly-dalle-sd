
  

# DILLY-DALLE

  

## Project Description

A telegram bot to interact with the DALL-E API to generate images and variations.

  
## Running the bot

The bot is available in [docker hub](https://hub.docker.com/r/valtimalti/dilly-dalle). Please refer to the repositroy there for the latest image version - the bot is still in development, with no latest release right now.

```
version: "3.9"
services:
	dillydalle:
		container_name: "dilly-dalle"
		image: valtimalti/dilly-dalle:latest-dev
		restart: always
		environment:
		- "LOGGING_LEVEL=INFO"
		- "TELEGRAM_BOT_TOKEN="
		- "OPENAI_API_TOKEN="
		- "BOT_USERNAME="
```

## Running a local image

After cloning the repository, adjust the  `docker-compose.yml` and run:

```

docker-compose up --build

```

Alternatively, you can run the Docker container directly:

```

docker run -d --name dilly-dalle -e LOGGING_LEVEL=INFO -e TELEGRAM_BOT_TOKEN=your_bot_token -e OPENAI_API_TOKEN=your_openai_token -e BOT_USERNAME=your_bot_username dilly-dalle

```

  
  

## Environment Variables

Configure the following environment variables in the `docker-compose.yml`:

  

| Variable | Description | Example Value |
|----------------------|-------------------------------------|---------------------|
| `LOGGING_LEVEL` | Set the logging level. | `INFO` |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token. | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `OPENAI_API_TOKEN` | Your OpenAI API token. | `sk-abcdef1234567890ghijklmn` |
| `BOT_USERNAME` | The username of your bot. | `my_telegram_bot` |


## Usage

Interact with the bot on Telegram using the following commands:

  

| Command | Description |
|--|--|
| `/picgen <prompt>` | Generates an image based on a text prompt. |
| `/variation ` | Create a variation of the image. Send it either as the caption of the image, or as a reply to an image. |
 | `/rephrase <prompt>` |  **IN TESTING** Rephrase an inappropriate prompt to fit within the DALLE API safety constraints. |
| `/describe` | **DISABLED FOR NOW** Describe a the provided person, object, or concept to fit within the DALLE API safety constraints. |
 



  

## Contributing

Contributions are welcome! Please follow these steps to contribute:

- Fork the repository.

- Create a new branch for your feature.

- Submit a pull request with a detailed description of your changes.

  

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE.md](LICENSE.md) file for details.
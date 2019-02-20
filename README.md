# music-bucket-bot

A Telegram Bot that collects streaming services music links that users send in a chat and shows them by request, with the related info:
- *Artist*
- *Album*
- *Track*

### Currently supported music streaming services:
- [x] Spotify
- [x] Deezer
- [ ] Tidal

### Commands
- ```/music``` Retrieves the music shared in the chat from the last week. Grouped by user.
- ```/music_from_beginning``` Retrieves the music shared in the chat from the beginning of time. Grouped by user.


**Official bot** => ```@music_telegram_bot```

## Installation
- Install dependencies from requirements.txt
- Copy the .env.dist file to .env and fill the variables with your Telegram and Spotify data.

## License
The content of this project is licensed under the GNU/GPLv3 license. See LICENSE file.

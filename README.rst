MusicBucket Bot
================

.. |full_logo| image:: https://github.com/paurieraf/musicbucket-bot/blob/master/images/logos/musicbucket_bot_letter_logo_1229x2574.png?raw=True

|full_logo|

About
~~~~~~~~

MusicBucket Bot is a Telegram Bot that adds features and possibility to interact with **Spotify** music links that users send in
a chat.

Its main feature is to allow you to **save links that someones shares in a Chat** in a personal list.
So you can easily track which music you have pending to listen to.

When an user sends a link, the bot is able to get information from a Spotify link like:

-  *Artist*
-  *Album*
-  *Track*
-  *Genres*
-  *Audio preview*

It also integrates with **Last.fm** to retrieve information about your
user like **Now Playing**.

Why Telegram?
_____________
I chose Telegram because I'm in a few groups where we share music everyday. We soon realized that
the links we shared in a group were often missed. Therefore, the idea of making a tool for keeping track
of the music we share started growing so I started developing this bot.

Why Spotify?
_____________
At the start the bot supported both Spotify and Deezer, but Spotify is the platform that we use
mostly, so implementing new features for both platforms is complicated and I decided supporting Spotify
only.


Commands
~~~~~~~~
-  ``/music [@username]`` Retrieves the music shared in the chat from
   the last week. Grouped by user. Filter by @username optionally.
-  ``/music_from_beginning @username`` Retrieves the music shared in the
   chat from the beginning of time by an user.
-  ``/savedlinks`` Retrieves a list with your saved links
-  ``/deletesavedlinks`` Shows a list of buttons for deleting saved links
-  ``/mymusic`` Retrieves the music that you shared in all the chats.
   It has to be called from a private conversation.
-  ``/np`` Now Playing. Returns track information about what you are
   currently playing in Last.fm.
-  ``/lastfmset username`` Sets a Last.fm username to your Telegram
   user.
-  ``/stats`` Retrieves an user list with a links counter for the
   current chat.
-  ``/help`` Retrieves a list of available commands and bot features.
-  ``@music_bucket_bot artist|album|track name`` Search for an artist,
   an album or a track and send it to the chat.

**Official bot** => ``@music_bucket_bot``

Screenshots
~~~~~~~~~~~

.. |screenshot_1| image:: https://github.com/paurieraf/musicbucket-bot/blob/master/images/screenshots/screenshot_1.jpg?raw=True
.. |screenshot_2| image:: https://github.com/paurieraf/musicbucket-bot/blob/master/images/screenshots/screenshot_2.jpg?raw=True
.. |screenshot_3| image:: https://github.com/paurieraf/musicbucket-bot/blob/master/images/screenshots/screenshot_3.jpg?raw=True
.. |screenshot_4| image:: https://github.com/paurieraf/musicbucket-bot/blob/master/images/screenshots/screenshot_4.jpg?raw=True

================================  ================================
|screenshot_1|                    |screenshot_3|

|screenshot_2|                    |screenshot_4|
================================  ================================


Installation
~~~~~~~~~~~~

-  Install ``pyenv`` and ``pipenv``
-  Do ``pipenv install`` inside the folder.
-  Copy the ``.env.dist`` file to ``.env`` and **fill the variables**
   with your Telegram and Spotify data.
-  Execute ``python main.py``


Special thanks
~~~~~~~~~~~~~~

- To Pablo I. for the logo.
- To the Sonomada community and its group in Telegram (https://t.me/Sonomada_gang) where we use and test the bot actively and propose new features.


License
~~~~~~~

The content of this project is licensed under the GNU/GPLv3 license. See
LICENSE file.



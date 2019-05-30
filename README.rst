Music Bucket Bot
================

A Telegram Bot that collects **Spotify** music links that users send in
a chat and shows them by request, with the related info: - *Artist* -
*Album* - *Track* - *Genres*

It also integrates with **Last.fm** to retrieve information about your
user like **Now Playing**.

Currently supported music streaming services:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  [x] Spotify

Commands
~~~~~~~~

-  ``/music [@username]`` Retrieves the music shared in the chat from
   the last week. Grouped by user. Filter by @username optionally.
-  ``/music_from_beginning @username`` Retrieves the music shared in the
   chat from the beginning of time by an user.
-  ``/recommendations`` Returns a list of 10 recommended tracks based on
   the sent albums from the last week.
-  ``/np`` Now Playing. Returns track information about what you are
   currently playing in Last.fm.
-  ``/lastfmset username`` Sets a Last.fm username to your Telegram
   user.
-  ``/stats`` Retrieves an user list with a links counter for the
   current chat.
-  ``@music_bucket_bot artist|album|track name`` Search for an artist,
   an album or a track and add it to the list.

**Official bot** => ``@music_bucket_bot``

Screenshots
____________

.. image:: https://github.com/paurieraf/musicbucket-bot/blob/master/images/screenshots/screenshot_1.jpg?raw=True
    :width: 24%
.. image:: https://github.com/paurieraf/musicbucket-bot/blob/master/images/screenshots/screenshot_2.jpg?raw=True
    :width: 24%
.. image:: https://github.com/paurieraf/musicbucket-bot/blob/master/images/screenshots/screenshot_3.jpg?raw=True
    :width: 24%
.. image:: https://github.com/paurieraf/musicbucket-bot/blob/master/images/screenshots/screenshot_4.jpg?raw=True
    :width: 24%



Installation
------------

-  Install ``pyenv`` and ``pipenv``
-  Do ``pipenv install`` inside the folder.
-  Copy the ``.env.dist`` file to ``.env`` and **fill the variables**
   with your Telegram and Spotify data.
-  Execute ``python main.py``

License
-------

The content of this project is licensed under the GNU/GPLv3 license. See
LICENSE file.

# Music League Data Scraper

This directory holds a set of utility scripts in Python which combine
to gather data from the Music League website and store them in a
SQLite Database.

The critical components are:

1. Authentication: The Music League website at https://musicleague.com must be traversed as an authenticated user, and users log in vial Spotify single sign on. So we first need a script or tool that can connect via the "Log In with Spotify" button on https://app.musicleague.com/login/ . This script could open a chrome window and await user credentials, request user credentials, or access local browser cache for an existing cookie - whatever method is best.

2. Traverse past leagues: Beginning on the
https://app.musicleague.com/completed/ page for the authenticated user
will be a list of league tiles for past leagues. For each such tile
traverse into that league, for example arriving at a page such as:

https://app.musicleague.com/l/ec277e0f0a4347f9b4629f611931cf47/

3. Scrape Data per league:

For each league, gather the following information:

* League Title
* List of rounds - for each round gather:
** Round Number
** Round Title
** Round Description

And then traverse into the Round Results page and gather detailed results for each round, arriving at a page such as:

https://app.musicleague.com/l/ec277e0f0a4347f9b4629f611931cf47/2288661f7ebf4d9cbfee40db2ffaa19a/

3a. Scrape Data per league round:

For each round there will be a list of songs, and each song has a list of comments and votes. Gather:

* Song Title
* Artist
* Album
* Total Votes
* Number of voters
* Submitting User
* Submitting User comments (optional)
* List of comments and votes, each of which contains:
** Voting user
** Voting comment (optional)
** Voting points (optional)

4. Store all data in database - All data should be stored in a sqlite
database with a data model which accomodates the relevant entities,
relations, and fields. As a baseline:

There is a leagues table with one row per league
  * This table also holds the league title

There is a rounds table with one row per league round and a foreign key to the leagues table
  * This table also holds the round number, round title, and round description

There is a songs table with one row per league round song and a foreign key to the rounds table's league and rounds columns
  * This table also holds the song title, artist, album, total votes, number of voters, submitting user, and submitting user comments

There is a comments table with one row per league round song comment and a foreign key to the songs table's league, rounds, and songs columns
  * This table also holds the voting user, voting comment, and voting points

4. Reports - There should be some reports available off the data in the SQLite database. Initial reports include:

* All songs - A list of each song submitted, in: song, artist, album, round description, league description format

* Distinct songs - An aggregated list of unique songs submitted in song, artist, submission_count format

* Best songs - The five songs with the highest total votes. If more than 5 songs would result because a number of songs tie on a given vote total, list all the songs with that vote total, in: song, artist, total votes, round description, league description format.

* Worst songs - The five songs with the lowest total votes. If more than 5 songs would result because a number of songs tie on a given vote total, list all the songs with that vote total, in: song, artist, total votes, round description, league description format.




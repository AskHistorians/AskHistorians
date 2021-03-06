import praw
import prawcore
from dotenv import load_dotenv
import os
import sys
import datetime
import pytz
from utils import *
import csv

class SaveFetcher():
    """Class that handles all of the internal work with reddit for fetching saves."""

    def __init__(self):
        pass

    def reddit_signin(self, username, password, twofac):
        """Method that handles reddit authentication with praw."""

        if not username or not password:
            return False, "Error: blank username/password!"

        load_dotenv()
        client_id = os.getenv("CLIENTID")
        client_secret = os.getenv("CLIENTSECRET")

        if twofac:
            password = password + ":" + twofac

        user_agent = "SaveFetcher:v1.0 (by u/AverageAngryPeasant)"
        self.reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent, username=username, password=password)

        try:
            self.reddit.user.me()
        except prawcore.ResponseException:
            return False, "Error: invalid credentials!"
        except Exception as e:
            print(e)
            if hasattr(e, 'message'):
                return False, "Error: " + e.message
            else:
                return False, "Error: " + str(e)
        else:
            return True, None

    def create_stamps(self, from_date, to_date):
        """Method that creates unix timestamps from dates, taking time zone into account."""

        self.from_stamp = get_unix_time(from_date)
        self.to_stamp = get_unix_time(to_date)
        if self.to_stamp < self.from_stamp:
            return False, "Error: from date after to date!"
        return True, None
        
    def saved_posts(self, unsave, name):
        """Method that fetches saved posts from a given subreddit and time period, exports its info, and then unsaves them."""

        try:
            saved = [post for post in self.reddit.user.me().saved(limit=None)]
            if not name:
                name = "results.csv"
            else:
                name = name + ".csv"

            with open(name, "w", newline="", encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Post Author", "Post Permalink", "Post Score", "Post Date", "Submission Author", "Submission Permalink", "Submission Score", "Submission Title"])
                for post in saved:
                    if post and type(post) is praw.models.Comment:
                        if post.subreddit.display_name == "AskHistorians" and self.from_stamp < post.created_utc < self.to_stamp:
                            line = [self.determine_deleted(post.author), post.permalink, post.score, get_date(post.created_utc).date(), self.determine_deleted(post.submission.author), post.submission.permalink, post.submission.score, post.submission.title]
                            writer.writerow(line)
                            if unsave:
                                post.unsave()
        except Exception as e:
            print(e)
            if hasattr(e, 'message'):
                return "Error: " + e.message
            else:
                return "Error: " + str(e)
        else:
            return "Success! Check this program's location for results."

    def determine_deleted(self, author):
        if author:
            return author.name
        else:
            return "[deleted]"

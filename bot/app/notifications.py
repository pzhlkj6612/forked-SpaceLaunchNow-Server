import json
import re

from django.utils.datetime_safe import datetime
import datetime as dtime
import pytz
from twitter import Twitter, OAuth, TwitterHTTPError
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.libraries.onesignalsdk import OneSignalSdk
from bot.utils.config import keys
from bot.models import Notification
from bot.utils.deserializer import launch_json_to_model
from bot.utils.util import seconds_to_time
import logging

AUTH_TOKEN_HERE = keys['AUTH_TOKEN_HERE']
APP_ID = keys['APP_ID']
DAEMON_SLEEP = 600
TAG = 'Notification Server'

# Get an instance of a logger
logger = logging.getLogger('bot.notifications')


def json_default(value):
    if isinstance(value, dtime.date):
        return dict(year=value.year, month=value.month, day=value.day)
    else:
        return value.__dict__


class NotificationServer:
    def __init__(self, debug=None, version=None):
        self.one_signal = OneSignalSdk(AUTH_TOKEN_HERE, APP_ID)
        if version is None:
            version = '1.3'
        self.launchLibrary = LaunchLibrarySDK(version=version)
        if debug is None:
            self.DEBUG = False
        else:
            self.DEBUG = debug
        response = self.one_signal.get_app(APP_ID)
        assert response.status_code == 200
        self.app = response.json()
        assert isinstance(self.app, dict)
        assert self.app['id'] and self.app['name'] and self.app['updated_at'] and self.app['created_at']
        self.app_auth_key = self.app['basic_auth_key']
        self.twitter = Twitter(
            auth=OAuth(keys['TOKEN_KEY'], keys['TOKEN_SECRET'], keys['CONSUMER_KEY'], keys['CONSUMER_SECRET'])
        )

    def send_to_twitter(self, message, notification):
        # Need to add actual twitter post here.

        if message.endswith(' (1/1)'):
            message = message[:-6]
        if len(message) > 120:
            end = message[-5:]
            if re.search("([1-9]*/[1-9])", end):
                message = (message[:111] + '... ' + end)
            else:
                message = (message[:117] + '...')
        logger.info('Sending to Twitter | %s | %s | DEBUG %s' % (message, str(len(message)), self.DEBUG))
        if not self.DEBUG:
            try:
                self.twitter.statuses.update(status=message)
            except TwitterHTTPError as e:
                logger.error("%s %s" % (str(e), message))

        notification.last_twitter_post = datetime.now()
        notification.last_net_stamp = notification.launch.netstamp
        notification.last_net_stamp_timestamp = datetime.now()
        logger.info('Updating Notification %s to timestamp %s' % (notification.launch.id,
                                                                  notification.last_twitter_post
                                                                  .strftime("%A %d. %B %Y")))

        notification.save()

    def get_next_launches(self):
        logger.info("Getting next launches...")
        response = self.launchLibrary.get_next_launch(count=5)
        if response.status_code is 200:
            response_json = response.json()
            launch_data = response_json['launches']
            launches = []
            for launch in launch_data:
                launch = launch_json_to_model(launch)
                if len(launch.location_set.all()[0].name) > 20:
                    launch.location_set.all()[0].name = launch.location_set.all()[0].name.split(", ")[0]
                else:
                    launch.location_set.all()[0].name = launch.location_set.all()[0].name
                launch.save()
                launches.append(launch)
            return launches
        else:
            logger.error(response.status_code + ' ' + response)

    def check_next_launch(self):
        for launch in self.get_next_launches():
            if launch.netstamp > 0:
                current_time = datetime.utcnow()
                launch_time = datetime.utcfromtimestamp(int(launch.netstamp))
                if current_time <= launch_time:
                    diff = int((launch_time - current_time).total_seconds())
                    logger.info('%s in %s hours' % (launch.name, (diff / 60) / 60))
                    self.check_launch_window(diff, launch)

    def netstamp_changed(self, launch, notification, diff):
        logger.info('Netstamp change detected for %s' % launch.name)
        date = datetime.fromtimestamp(launch.netstamp).replace(tzinfo=pytz.UTC)
        message = 'SCHEDULE UPDATE: %s now launching in %s at %s.' % (launch.name,
                                                                      seconds_to_time(diff),
                                                                      date.strftime("%H:%M %Z (%d/%m)"))
        launch.save()
        self.send_to_twitter(message, notification)

        # If launch is within 24 hours...
        if 86400 >= diff > 3600:
            logger.info('Launch is within 24 hours, resetting notifications.')
            notification.wasNotifiedTwentyFourHour = True
            notification.wasNotifiedOneHour = False
            notification.wasNotifiedTenMinutes = False
        elif 3600 >= diff > 600:
            logger.info('Launch is within one hour, resetting Ten minute notifications.')
            notification.wasNotifiedOneHour = True
            notification.wasNotifiedTwentyFourHour = True
            notification.wasNotifiedTenMinutes = False
        elif diff <= 600:
            logger.info('Launch is within ten minutes hour.')
            notification.wasNotifiedOneHour = True
            notification.wasNotifiedTwentyFourHour = True
            notification.wasNotifiedTenMinutes = True
        notification.save()

    def check_twitter(self, diff, launch, notification):
        logger.info('Diff - %d for %s' % (diff, launch.name,))
        logger.debug('LAUNCH DATA: %s', json.dumps(launch, default=lambda o: o.__dict__))
        logger.debug('NOTIFICAITON DATA: %s', json.dumps(notification, default=json_default))
        if (notification.last_net_stamp is not None or 0)\
                and abs(notification.last_net_stamp - launch.netstamp) > 600\
                and diff <= 259200:
            self.netstamp_changed(launch, notification, diff)
        elif notification.last_twitter_post is not None:
            time_since_twitter = (datetime.now() - notification.last_twitter_post).total_seconds()
            logger.info('Seconds since last update on Twitter %d for %s' % (time_since_twitter,
                                                                            launch.name))
            if diff <= 86400 and notification.wasNotifiedTwentyFourHour is False:
                message = '%s | %s launching from %s in %s.' % (launch.name, launch.mission_name, launch.location_set.all()[0].name,
                                                                seconds_to_time(diff))
                logger.info(message)
                self.send_to_twitter(message, notification)
            elif 3600 >= diff > 600 and time_since_twitter >= 43200 and notification.wasNotifiedOneHour is False:
                message = '%s | %s launching from %s in %s.' % (launch.name, launch.mission_name, launch.location_set.all()[0].name,
                                                                seconds_to_time(diff))
                logger.info(message)
                self.send_to_twitter(message, notification)
            elif diff <= 600 and (time_since_twitter >= 600) and notification.wasNotifiedOneHour is False:
                message = '%s | %s launching from %s in %s.' % (launch.name, launch.mission_name, launch.location_set.all()[0].name,
                                                                seconds_to_time(diff))
                logger.info(message)
                self.send_to_twitter(message, notification)
        elif notification.last_twitter_post is None:
            if diff <= 86400:
                message = '%s | %s launching from %s in %s.' % (launch.name, launch.mission_name, launch.location_set.all()[0].name,
                                                                seconds_to_time(diff))
                logger.info(message)
                self.send_to_twitter(message, notification)
            elif 3600 >= diff > 600:
                message = '%s | %s launching from %s in %s.' % (launch.name, launch.mission_name, launch.location_set.all()[0].name,
                                                                seconds_to_time(diff))
                logger.info(message)
                self.send_to_twitter(message, notification)
            elif diff <= 600:
                message = '%s | %s launching from %s in %s.' % (launch.name, launch.mission_name, launch.location_set.all()[0].name,
                                                                seconds_to_time(diff))
                logger.info(message)
                self.send_to_twitter(message, notification)

    def check_launch_window(self, diff, launch):
        notification = Notification.objects.get(launch=launch)
        self.check_twitter(diff, launch, notification)
        logger.info('Checking launch window for %s' % notification.launch.name)

        # If launch is within 24 hours...
        if 86400 >= diff > 3600 and not notification.wasNotifiedTwentyFourHour:
            logger.info('Launch is within 24 hours, sending notifications.')
            self.send_notification(launch)
            notification.wasNotifiedTwentyFourHour = True
        elif 3600 >= diff > 600 and not notification.wasNotifiedOneHour:
            logger.info('Launch is within one hour, sending notifications.')
            self.send_notification(launch)
            notification.wasNotifiedOneHour = True
        elif diff <= 600 and not notification.wasNotifiedTenMinutes:
            logger.info('Launch is within ten minutes, sending notifications.')
            self.send_notification(launch)
            notification.wasNotifiedTenMinutes = True
        else:
            logger.info('%s does not meet notification criteria.' % notification.launch.name)
        notification.save()

    def send_notification(self, launch):
        self.one_signal.user_auth_key = self.app_auth_key
        self.one_signal.app_id = APP_ID
        logger.info('Creating notification for %s' % launch.name)

        # Create a notification
        contents = '%s launching from %s' % (launch.name, launch.location_set.all()[0].name)
        kwargs = dict(
            content_available=True,
            included_segments=['Debug'],
            isAndroid=True,
            data={"silent": True,
                  "background": True,
                  "launch_id": launch.id,
                  "launch_name": launch.name,
                  "launch_image": launch.rocket_set.all()[0].imageURL,
                  "launch_net": launch.net,
                  "launch_location": launch.location_set.all()[0].name,
                  "launch_lsp": launch.lsp_set.all()[0].id,
                  "launch_rocket_agency": launch.rocket_set.all()[0].agency_set.all()[0].id,
                  "launch_location_agency": launch.location_set.all()[0].pad_set.all()[0].agency_set.all()[0].id}
        )
        url = 'https://spacelaunchnow.me/launch/%d/' % launch.id
        heading = 'Space Launch Now'
        if not self.DEBUG:
            logger.debug('Sending notification - %s' % contents)
            response = self.one_signal.create_notification(contents, heading, url, **kwargs)
            if response.status_code == 200:
                logger.info('Response received %s %s' % (response.status_code, response.json()))
            else:
                logger.error(response.text)

            notification_data = response.json()
            notification_id = notification_data['id']
            assert notification_data['id'] and notification_data['recipients']

            # Get the notification
            response = self.one_signal.get_notification(APP_ID, notification_id, self.app_auth_key)
            notification_data = response.json()
            assert notification_data['id'] == notification_id
            assert notification_data['contents']['en'] == contents

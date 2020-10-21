"""Weekend video tasks cog"""
import discord
import logging
from services.config import config
from discord.ext.commands import Cog
from apscheduler.triggers.cron import CronTrigger

class WeekendVideoTasks(Cog):
    """Tasks for sending weekend videos"""

    def __init__(self, bot):
        self.bot = bot
        self.friday_video_job = self.bot.scheduler.add_job(
            self.send_friday_video,
            CronTrigger(
                day_of_week=4,  # Friday
                hour=18,        # 6:00 PM
                minute=0,
                second=0,
                timezone='EST5EDT'
            )
        )
        next_run_time = self.friday_video_job.next_run_time.strftime('%Y-%m-%d %I:%M %p')
        logging.info(f'"WeekendVideoTasks.send_friday_video" next run time: {next_run_time}')

        self.saturday_video_job = self.bot.scheduler.add_job(
            self.send_saturday_video,
            CronTrigger(
                day_of_week=5,  # Saturday
                hour=10,        # 10:00 AM
                minute=0,
                second=0,
                timezone='EST5EDT'
            )
        )
        next_run_time = self.saturday_video_job.next_run_time.strftime('%Y-%m-%d %I:%M %p')
        logging.info(f'"WeekendVideoTasks.send_saturday_video" next run time: {next_run_time}')

        self.sunday_video_job = self.bot.scheduler.add_job(
            self.send_sunday_video,
            CronTrigger(
                day_of_week=6,  # Sunday
                hour=12,        # 12:00 PM
                minute=0,
                second=0,
                timezone='EST5EDT'
            )
        )
        next_run_time = self.sunday_video_job.next_run_time.strftime('%Y-%m-%d %I:%M %p')
        logging.info(f'"WeekendVideoTasks.send_sunday_video" next run time: {next_run_time}')

    async def send_friday_video(self):
        """Send the friday videos"""
        await self.bot.general_channel.send(config.FRIDAY_VIDEO_1)
        await self.bot.general_channel.send(config.FRIDAY_VIDEO_2)
        next_run_time = self.friday_video_job.next_run_time.strftime('%Y-%m-%d %I:%M %p')
        logging.info(f'"WeekendVideoTasks.send_friday_video" next run time: {next_run_time}')

    async def send_saturday_video(self):
        """Send the saturday video"""
        await self.bot.general_channel.send(config.SATURDAY_VIDEO_1)
        await self.bot.general_channel.send(config.SATURDAT_VIDEO_2)
        next_run_time = self.saturday_video_job.next_run_time.strftime('%Y-%m-%d %I:%M %p')
        logging.info(f'"WeekendVideoTasks.send_saturday_video" next run time: {next_run_time}')

    async def send_sunday_video(self):
        """Send the sunday videos"""
        await self.bot.general_channel.send(config.SUNDAY_VIDEO_1)
        await self.bot.general_channel.send(config.SUNDAY_VIDEO_2)
        next_run_time = self.sunday_video_job.next_run_time.strftime('%Y-%m-%d %I:%M %p')
        logging.info(f'"WeekendVideoTasks.send_sunday_video" next run time: {next_run_time}')

def setup(bot):
    """Add this cog"""
    bot.add_cog(WeekendVideoTasks(bot))

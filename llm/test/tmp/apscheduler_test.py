import asyncio
import logging

from apscheduler.triggers.cron import CronTrigger

from app.config.scheduler_config.scheduler_config_repository import scheduler_config_repository
from app.config.scheduler_config.scheduler_config_runner import SchedulerConfigRunner
from app.config.scheduler_config.scheduler_handler import SchedulerHandler, SchedulerEnum
from app.tool.class_tool import ClassTool

# set logger
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# set event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# set apscheduler
scheduler_config_runner = SchedulerConfigRunner()
scheduler_config_runner.run(loop=loop)
scheduler_handler = SchedulerHandler(scheduler_config_repository)

print(scheduler_handler.get_state())

scheduler_handler.handle(SchedulerEnum.Task.START)

print(scheduler_handler.get_state())

scheduler_handler.add_job_with_cron(
    job=ClassTool.get_instance_method(
        module_name="app.job.sleep.sleep_job",
        class_name="SleepJob",
        method_name="task"
    ),
    cron=CronTrigger(year="*", month="*", day="*", hour="*", minute="*", second="*/10", timezone="Asia/Seoul"),
)

# scheduler_handler.add_job_with_cron(
#     job=ClassTool.get_instance_method(
#         module_name="app.job.cmd.cmd_job",
#         class_name="CmdJob",
#         method_name="task"
#     ),
#     cron=CronTrigger(year="*", month="*", day="*", hour="*", minute="*/10", second="0", timezone="Asia/Seoul"),
# )
#
# scheduler_handler.add_job_with_interval(
#     job=ClassTool.get_instance_method(
#         module_name="app.job.sample.sample_job",
#         class_name="SampleJob",
#         method_name="task"
#     ),
#     interval_seconds=30
# )

for job in scheduler_handler.get_jobs():
    print(scheduler_handler.get_job(job.id))

loop.run_forever()

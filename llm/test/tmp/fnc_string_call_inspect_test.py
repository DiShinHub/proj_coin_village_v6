import asyncio
import inspect

module_name = "app.job.sample.sample_job"
class_name = "SampleJob"
method_name = "task"

module = __import__("%s" % (module_name), fromlist=[module_name])
module_member_list = inspect.getmembers(module, inspect.isclass)

if module_member_list:
    clazz = getattr(module, class_name)
    instance = clazz()
    fnc = getattr(instance, method_name)
    if inspect.iscoroutinefunction(fnc):
        asyncio.run(fnc())
    else:
        fnc()

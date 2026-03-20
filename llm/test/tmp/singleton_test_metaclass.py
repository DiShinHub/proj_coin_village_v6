class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class TestClass(metaclass=Singleton):
    def __init__(self, param1: str = "param1"):
        self.param1 = param1

    def get_param1(self):
        return self.param1

    @staticmethod
    def get_static():
        return "static"


test_class1 = TestClass(param1="not change")
test_class2 = TestClass(param1="changed")
print(test_class1)
print(test_class2)
print(test_class1.get_param1())
print(test_class2.get_param1())
print(TestClass.get_static())

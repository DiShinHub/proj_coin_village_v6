class TestClass:
    a: int = 0

    def __init__(self):
        self.b = 1

    @classmethod
    def getNumberClass(cls):
        return cls.a

    @classmethod
    def setNumberClass(cls, a: int):
        cls.a = a

    def getNumberInstanceA(self):
        return self.a

    def getNumberInstanceB(self):
        return self.b

    def setNumberInstanceA(self, a: int):
        self.a = a

    def setNumberInstanceB(self, b: int):
        self.b = b

    @staticmethod
    def getNumber():
        return None


test_class1 = TestClass()
test_class2 = TestClass()

print(test_class1.getNumberClass())
print(test_class2.getNumberClass())
print(TestClass.getNumberClass())

test_class2.setNumberClass(10)
test_class2.setNumberInstanceA(10)
test_class2.setNumberInstanceB(10)

print(test_class1.getNumberClass())
print(test_class2.getNumberClass())
print(test_class1.getNumberInstanceA())
print(test_class2.getNumberInstanceA())
print(test_class1.getNumberInstanceB())
print(test_class2.getNumberInstanceB())
print(TestClass.getNumberClass())

print(TestClass.a)
a = {"test": {"test_key": "test_value"}}


def convert(_dict: dict):
    b = a["test"]
    b["test_key"] = "test_value3"


convert(a)
print(a)

if "test2" in a:
    print("ok")

b = ["a", "b", "c"]
for index, value in enumerate(b):
    print(index)
    print(value)


a = list()
print(a.append("b"))
print(a)
class Test:
    def __init__(self):
        print("init")

    def __call__(self, *args, **kwargs):
        print("call")


if __name__ == "__main__":
    Test()()

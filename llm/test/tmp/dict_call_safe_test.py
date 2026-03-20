a = dict(
    test1="test1",
    test2="test2"
)

# unsafe
try:
    print(a["test"])
except Exception as e:
    print(f"get Exeption = [{e}]")

# safe
try:
    print(a.get("test"))
except Exception as e:
    print(f"get Exeption = [{e}]")

# safe
try:
    print(a.get("test", "default_value"))
except Exception as e:
    print(f"get Exeption = [{e}]")
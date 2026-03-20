import re

pattern = re.compile("^/api/[^/]*/au")
print(pattern.match("/api/v1/au/test"))
print(pattern.match("/api/v1/na/test"))
print(pattern.match("a/api/v1/au/test"))

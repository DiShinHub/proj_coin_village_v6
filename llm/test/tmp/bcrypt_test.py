import bcrypt

print(bcrypt.hashpw("1234qwer".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"))
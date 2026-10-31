import bcrypt


class BcryptPasswordEncoder:
    def encode(self, raw_password: str) -> str:
        hashed = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt(rounds=10))
        return hashed.decode("utf-8")

    def matches(self, raw_password: str, encoded_password: str) -> bool:
        try:
            return bcrypt.checkpw(raw_password.encode("utf-8"), encoded_password.encode("utf-8"))
        except ValueError:
            return False

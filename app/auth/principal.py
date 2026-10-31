from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    user_id: str
    email: str
    roles: frozenset[str]

    def has_any_role(self, *roles: str) -> bool:
        return bool(self.roles.intersection(roles))

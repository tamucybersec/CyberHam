from cyberham.dynamodb.dynamo import DynamoDB
from cyberham.dynamodb.types import TableName, User, UserData, MaybeItem


class UsersDB:
    db: DynamoDB
    table: TableName = "users"

    def __init__(self) -> None:
        self.db = DynamoDB()

    def get_user(self, user_id: int) -> User:
        key = self.db.create_key("users", str(user_id)) # TODO: temp values
        item = self.db.get_item(self.table, key)
        return self._item_to_user(item)

    def create_user(self, user: User) -> None:
        data = {"temp": "temp"} # TODO: temp values (turn user into a dict)
        self.db.put_item(self.table, data)

    def get_or_create_user(self, user_id: int) -> User:
        try:
            return self.get_user(user_id)
        except:
            return None

    def _item_to_user(self, item: MaybeItem) -> User:
        if item == None:
            return None

        return UserData(
            user_id=int(str(item.get("user_id", "0"))),
            name=str(item.get("name", "")),
            points=int(str(item.get("points", "0"))),
            attended=int(str(item.get("attended", "0"))),
            grad_year=int(str(item.get("grad_year", "0"))),
            email=str(item.get("email", "")),
        )


usersdb = UsersDB()

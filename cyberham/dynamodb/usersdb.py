from cyberham.dynamodb.dynamo import DynamoDB
from cyberham.dynamodb.types import Tables, User, UserData, Item


class UsersDB:
    db: DynamoDB
    table: Tables = "users"

    def __init__(self) -> None:
        self.db = DynamoDB()

    def get_user(self, user_id: int) -> User:
        item = self.db.get_item(self.table, str(user_id))
        return self._item_to_user(item)

    def create_user(self, user: User) -> None:
        self.db.put_item(self.table, user)

    def get_or_create_user(self, user_id: int) -> User:
        try:
            return self.get_user(user_id)
        except:
            return None

    def _item_to_user(self, item: Item) -> User:
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

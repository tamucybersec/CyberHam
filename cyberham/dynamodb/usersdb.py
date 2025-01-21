from cyberham.dynamodb.dynamo import DynamoDB
from cyberham.dynamodb.types import (
    TableName,
    MaybeUser,
    User,
    data_to_item,
    item_to_data,
)


class UsersDB:
    db: DynamoDB
    table: TableName = "users"

    def __init__(self) -> None:
        self.db = DynamoDB()

    def create_user(self, user: User) -> None:
        item = data_to_item(user)

        if item is None:
            raise TypeError(
                "This code is impossible to reach but the compiler demands I write it."
            )

        self.db.put_item(self.table, item)

    def get_user(self, user_id: int) -> MaybeUser:
        key = self.db.create_key("users", str(user_id))
        item = self.db.get_item(self.table, key)
        return item_to_data(item, User)
    
    # def 

    def get_or_create_user(self, user_id: int) -> User:
        """
        Gets the user if they exist, otherwise creates one with the given id.
        """

        raise Exception("Unimplemented")

        # user = self.get_user(user_id)
        # if user is not None:
        #     return user

        # return self.create_user(user_id)


usersdb = UsersDB()

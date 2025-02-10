from cyberham.dynamodb.dynamo import DynamoDB
from cyberham.dynamodb.types import (
    TableName,
    MaybeUser,
    User,
    UpdateUser,
    data_to_item,
    item_to_data,
    Key,
)


class UsersDB:
    db: DynamoDB
    table: TableName = "users"

    def __init__(self) -> None:
        self.db = DynamoDB()

    def put_user(self, user: User) -> None:
        item = data_to_item(user)

        if item is None:
            raise TypeError(
                "This code is impossible to reach but the compiler demands I write it."
            )

        self.db.put_item(self.table, item)

    def get_user(self, user_id: int) -> MaybeUser:
        key = self._get_key(user_id)
        item = self.db.get_item(self.table, key)
        return item_to_data(item, User)

    def update_user(self, user_id: int, update: UpdateUser) -> MaybeUser:
        """
        Access an user, change its contents, and the upload the change.
        The accessed user can be None (the user doesn't exist) and you can return None (delete the user).
        Returns the updated user.
        """

        get_user = self.get_user(user_id)
        updated_user = update(get_user)

        if updated_user is None:
            self.delete_user(user_id)
            return None
        else:
            self.put_user(updated_user)
            return updated_user

    def delete_user(self, user_id: int) -> MaybeUser:
        """
        Returns the user that was deleted.
        """

        key = self._get_key(user_id)
        item = self.db.delete_item(self.table, key)
        return item_to_data(item, User)

    def get_all(self) -> list[User]:
        items = self.db.get_all(self.table)

        users: list[User] = []
        for item in items:
            users.append(item_to_data(item, User))  # type: ignore

        return users

    def get_count(self) -> int:
        return len(self.db.get_all_raw(self.table))

    def _get_key(self, user_id: int) -> Key:
        return self.db.create_key("users", str(user_id))


usersdb = UsersDB()

import boto3
from cyberham import dynamo_keys
from mypy_boto3_dynamodb import DynamoDBClient
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from cyberham.dynamodb.types import (
    TableName,
    Item,
    MaybeItem,
    SerializedItem,
    Key,
    SerializedDict,
    UpdateItem,
)

DEFAULT_REGION = "us-east-1"


class DynamoDB:
    dynamodb: DynamoDBClient
    serializer: TypeSerializer
    deserializer: TypeDeserializer

    def __init__(
        self,
        region: str = DEFAULT_REGION,
    ) -> None:
        self.dynamodb = boto3.client(  # type: ignore
            "dynamodb",
            aws_access_key_id=dynamo_keys["access_key_id"],
            aws_secret_access_key=dynamo_keys["secret_access_key"],
            region_name=region,
        )

        self.serializer = TypeSerializer()
        self.deserializer = TypeDeserializer()

    def put_item(self, table: TableName, item: Item) -> MaybeItem:
        """
        Returns the item the operation overwrote, if any.
        """

        serialized = self._serialize(item)
        response = self.dynamodb.put_item(
            TableName=table, Item=serialized, ReturnValues="ALL_OLD"
        )
        old_item: SerializedItem | None = response.get("Attributes")

        if old_item:
            return self._deserialize(old_item)

        return None

    def get_item(
        self,
        table: TableName,
        key: Key,
    ) -> MaybeItem:
        """
        Get the item with the corresponding key, if it exists.
        """

        serialized = self._serialize(key)
        response = self.dynamodb.get_item(TableName=table, Key=serialized)
        item: SerializedItem | None = response.get("Item")

        if item:
            return self._deserialize(item)

        return None

    def update_item(self, table: TableName, key: Key, update: UpdateItem) -> MaybeItem:
        """
        Access an item, change its contents, and the upload the change.
        The accessed item can be None (the item is new) and you can return None (delete the existing item).
        Returns the new item following the update.
        """

        get_item = self.get_item(table, key)
        updated_item = update(get_item)

        if updated_item is None:
            self.delete_item(table, key)
            return None
        else:
            self.put_item(table, updated_item)
            return updated_item

    def delete_item(self, table: TableName, key: Key) -> MaybeItem:
        """
        Returns the item that was deleted.
        """

        serialized = self._serialize(key)
        response = self.dynamodb.delete_item(
            TableName=table, Key=serialized, ReturnValues="ALL_OLD"
        )
        old_item: SerializedItem | None = response.get("Attributes")

        if old_item:
            return self._deserialize(old_item)

        return None

    def create_key(
        self,
        partition_key_name: str,
        partition_key: str,
        sort_key_name: str = "",
        sort_key: str = "",
    ) -> Key:
        if sort_key_name is not "" and sort_key is not "":
            return {
                partition_key_name: partition_key,
                sort_key_name: sort_key,
            }
        else:
            return {partition_key_name: partition_key}

    def _serialize(self, key: Key) -> SerializedDict:
        return {k: self.serializer.serialize(v) for k, v in key.items()}

    def _deserialize(self, item: SerializedItem) -> Item:
        return {k: self.deserializer.deserialize(v) for k, v in item.items()}  # type: ignore

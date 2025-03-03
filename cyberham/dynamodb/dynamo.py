import boto3
from mypy_boto3_dynamodb.type_defs import ScanOutputTypeDef
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
    _dynamodb: DynamoDBClient
    _serializer: TypeSerializer
    _deserializer: TypeDeserializer

    def __init__(
        self,
        region: str = DEFAULT_REGION,
    ) -> None:
        self._dynamodb = boto3.client(
            "dynamodb",
            aws_access_key_id=dynamo_keys["access_key_id"],
            aws_secret_access_key=dynamo_keys["secret_access_key"],
            region_name=region,
        )

        self._serializer = TypeSerializer()
        self._deserializer = TypeDeserializer()

    def put_item(self, table: TableName, item: Item) -> MaybeItem:
        """
        Returns the item the operation overwrote, if any.
        """

        serialized = self._serialize(item)
        response = self._dynamodb.put_item(
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
        response = self._dynamodb.get_item(TableName=table, Key=serialized)
        item: SerializedItem | None = response.get("Item")

        if item:
            return self._deserialize(item)

        return None

    def update_item(self, table: TableName, key: Key, update: UpdateItem) -> MaybeItem:
        """
        Access an item, change its contents, and the upload the change.
        The accessed item can be None (the item doesn't exist) and you can return None (delete the item).
        Returns the updated item.
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
        response = self._dynamodb.delete_item(
            TableName=table, Key=serialized, ReturnValues="ALL_OLD"
        )
        old_item: SerializedItem | None = response.get("Attributes")

        if old_item:
            return self._deserialize(old_item)

        return None

    def get_all(self, table: TableName) -> list[Item]:
        result: ScanOutputTypeDef = self._dynamodb.scan(TableName=table)
        items: list[SerializedItem] | None = result.get("Items")

        deserialized: list[Item] = []
        for item in items:
            deserialized.append(self._deserialize(item))

        return deserialized

    def get_count(self, table: TableName) -> int:
        result: ScanOutputTypeDef = self._dynamodb.scan(TableName=table)
        return result.get("Count")

    @staticmethod
    def create_key(
        partition_key_name: str,
        partition_key: str | int,
        sort_key_name: str = "",
        sort_key: str = "",
    ) -> Key:
        if sort_key_name != "" and sort_key != "":
            return {
                partition_key_name: partition_key,
                sort_key_name: sort_key,
            }
        else:
            return {partition_key_name: partition_key}

    def _serialize(self, key: Key) -> SerializedDict:
        return {k: self._serializer.serialize(v) for k, v in key.items()}

    def _deserialize(self, item: SerializedItem) -> Item:
        return {k: self._deserializer.deserialize(v) for k, v in item.items()}  # type: ignore

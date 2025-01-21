from cyberham.dynamodb.types import Item, TableName

table: TableName = "tests"
partition_key: str = "partition"
sort_key: str = "sort"

existing_item: Item = {partition_key: "0", sort_key: "0", "name": "some_name"}
non_existent_item: Item = {partition_key: "-1", sort_key: "-1", "name": "no_name"}
new_item: Item = {partition_key: "1", sort_key: "1", "name": "new_name"}
update_item: Item = {partition_key: "2", sort_key: "2", "name": "updated_name"}

class Inventory:
    def __init__(self):
        self.items = []

    def add_item(self, item: dict) -> None:
        """Add an item to inventory. Item is a dict with at least 'name' and optional other properties."""
        self.items.append(item)

    def remove_item(self, item_name: str) -> bool:
        """Remove an item by name. Returns True if removed, False if not found."""
        for i, item in enumerate(self.items):
            if item.get("name") == item_name:
                self.items.pop(i)
                return True
        return False

    def has_item(self, item_name: str) -> bool:
        """Check if inventory contains an item by name."""
        return any(item.get("name") == item_name for item in self.items)

    def get_items_by_name(self, item_name: str) -> list:
        """Get all items with a specific name."""
        return [item for item in self.items if item.get("name") == item_name]

def get_first_item(items):
    if not items:
        return None
    return items[0]

# Deliberate Crash Trigger
get_first_item([])

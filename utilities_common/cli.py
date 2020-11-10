import json

def json_dump(data):
    """
    Dump data in JSON format
    """
    return json.dumps(
        data, sort_keys=True, indent=2, ensure_ascii=False
    )

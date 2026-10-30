import requests
import pandas as pd


json_msg = requests.get("http://api.brain-map.org/api/v2/structure_graph_download/1.json")


def parse_hierarchy(json_part):
    """
    Recursively flattens a hierarchy by appending children
    and then removing the 'children' field.
    """
    flattened = []

    for child in json_part.get("children", []):
        if child.get("children"):
            flattened.extend(parse_hierarchy(child))
        else:
            flattened.append(child)

    # Remove children after processing
    json_part = dict(json_part)
    json_part["children"] = []

    return [json_part] + flattened


# ---- Run hierarchy parsing ----
df = parse_hierarchy(json_msg.json())

# Flatten list of dicts into a single list (mimics R's c())
flat = []
for item in df:
    flat.extend(list(item.values()))

# ---- Equivalent of df2 ----
df2 = pd.DataFrame({
    "id":       flat[0::11],
    "name":     flat[4::11],
    "acronym":  flat[3::11]
})

df2.to_csv("brainStructureMappingTable.csv", index=False)

# ---- Equivalent of df3 ----
df3 = pd.DataFrame({
    "child":  flat[0::11],
    "parent": [None] + flat[9::11]
})

df3.to_csv("parentChildStructure.csv", index=False)
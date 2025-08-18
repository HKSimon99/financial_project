#!/usr/bin/env python3
import csv
from backend.main import app


def _collect_fields(schema, node):
    if "$ref" in node:
        name = node["$ref"].split("/")[-1]
        return _collect_fields(schema, schema["components"]["schemas"][name])
    props = node.get("properties", {})
    fields = set(props.keys())
    for key, val in props.items():
        fields |= _collect_fields(schema, val)
    return fields


if __name__ == "__main__":
    spec = app.openapi()
    rows = set()
    for path, methods in spec["paths"].items():
        for meta in methods.values():
            content = meta.get("responses", {}).get("200", {}).get("content", {})
            schema = next(iter(content.values()), {}).get("schema")
            if schema:
                for field in _collect_fields(spec, schema):
                    rows.add((path, field))
    with open("/tmp/api_fields.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "field"])
        writer.writerows(sorted(rows))

# Exact recipe format

A recipe is deliberately explicit and fail-closed.

```json
{
  "recipes": {
    "example": {
      "operations": [
        {
          "type": "replace_text",
          "file": "smali/example.smali",
          "find": "EXACT_SOURCE_SEQUENCE",
          "replace": "EXACT_REPLACEMENT_SEQUENCE",
          "count": 1,
          "min_matches": 1,
          "description": "Example exact patch"
        }
      ]
    }
  }
}
```

For a real MIUI/HyperOS release, add a recipe only after validating the decoded file/class/method for that release. A recipe with zero matches stops rather than modifying a different implementation.

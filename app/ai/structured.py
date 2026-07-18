"""Flash-Lite structured-output helper.

Council verdict (ITEM 5): Flash-Lite is reliable for structured JSON
(~0.39% schema-fail), BUT it ignores schema `description` fields. Rules:
  - put instructions in the prompt, NOT in schema descriptions
  - keep schema string fields < 200 tokens
  - validate once per credential; provider-owned repair uses another pool slot
  - transport failures are retried by the provider credential pool, never on
    the same credential inside this helper
  - model = gemini-3.1-flash-lite (NOT non-lite flash for structured output)
"""
from pydantic import BaseModel, ValidationError

STRUCTURED_MODEL = "gemini-3.1-flash-lite"

def _gemini_response_schema(schema_cls: type[BaseModel]) -> dict:
    """Return the pinned Gemini SDK's JSON-Schema subset.

    Pydantic remains the authoritative validator after generation. The wire
    schema is intentionally a compatible superset when tuple-position or
    ``extra='forbid'`` constraints cannot be represented by Gemini.
    """

    raw_schema = schema_cls.model_json_schema()
    definitions = raw_schema.get("$defs", {})
    allowed_keys = {
        "description",
        "enum",
        "example",
        "format",
        "items",
        "maxItems",
        "maxLength",
        "maxProperties",
        "maximum",
        "minItems",
        "minLength",
        "minProperties",
        "minimum",
        "nullable",
        "pattern",
        "properties",
        "propertyOrdering",
        "required",
        "title",
        "type",
    }

    def merge_wire_schemas(schemas: list[dict]) -> dict:
        candidates = [schema for schema in schemas if schema]
        if not candidates:
            return {}
        nullable = any(schema.get("type") == "null" for schema in candidates)
        candidates = [schema for schema in candidates if schema.get("type") != "null"]
        if not candidates:
            return {"nullable": True}
        if len(candidates) == 1:
            result = dict(candidates[0])
            if nullable:
                result["nullable"] = True
            return result

        schema_types = {schema.get("type") for schema in candidates}
        if len(schema_types) != 1 or None in schema_types:
            result = dict(candidates[0])
            if nullable:
                result["nullable"] = True
            return result

        schema_type = next(iter(schema_types))
        result: dict = {"type": schema_type}
        if nullable:
            result["nullable"] = True

        if schema_type == "object":
            property_names = {
                name
                for schema in candidates
                for name in (schema.get("properties") or {})
            }
            result["properties"] = {
                name: merge_wire_schemas(
                    [
                        schema["properties"][name]
                        for schema in candidates
                        if name in (schema.get("properties") or {})
                    ]
                )
                for name in sorted(property_names)
            }
            required_sets = [set(schema.get("required") or []) for schema in candidates]
            required = set.intersection(*required_sets) if required_sets else set()
            if required:
                result["required"] = sorted(required)
        elif schema_type == "array":
            item_schemas = [
                schema["items"] for schema in candidates if schema.get("items")
            ]
            if item_schemas:
                result["items"] = merge_wire_schemas(item_schemas)
            minimums = [schema["minItems"] for schema in candidates if "minItems" in schema]
            maximums = [schema["maxItems"] for schema in candidates if "maxItems" in schema]
            if minimums:
                result["minItems"] = min(minimums)
            if maximums:
                result["maxItems"] = max(maximums)
        else:
            enums = [schema.get("enum") for schema in candidates]
            if all(enum is not None for enum in enums):
                result["enum"] = list(
                    dict.fromkeys(
                        value
                        for enum in enums
                        for value in (enum or [])
                    )
                )

        for key in ("format", "pattern"):
            values = [schema.get(key) for schema in candidates]
            if values and values[0] is not None and all(value == values[0] for value in values):
                result[key] = values[0]
        return result

    def normalize(value, resolving: tuple[str, ...] = ()):
        if isinstance(value, list):
            return [normalize(item, resolving) for item in value]
        if not isinstance(value, dict):
            return value

        reference = value.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/$defs/"):
            name = reference.rsplit("/", 1)[-1]
            if name in resolving or name not in definitions:
                return {}
            merged = {
                **definitions[name],
                **{key: item for key, item in value.items() if key != "$ref"},
            }
            return normalize(merged, (*resolving, name))

        any_of = value.get("anyOf")
        if isinstance(any_of, list) and any_of:
            merged_options = merge_wire_schemas(
                [normalize(option, resolving) for option in any_of]
            )
            remaining = {
                key: item
                for key, item in value.items()
                if key != "anyOf"
            }
            return {
                **merged_options,
                **normalize(remaining, resolving),
            }

        normalized: dict = {}
        if "const" in value:
            normalized["enum"] = [normalize(value["const"], resolving)]

        prefix_items = value.get("prefixItems")
        if isinstance(prefix_items, list) and prefix_items:
            item_schemas = [normalize(item, resolving) for item in prefix_items]
            normalized["items"] = (
                item_schemas[0]
                if len(item_schemas) == 1
                else merge_wire_schemas(item_schemas)
            )

        for key, item in value.items():
            if key in {"$defs", "$ref", "additionalProperties", "const", "default", "prefixItems"}:
                continue
            if key not in allowed_keys:
                continue
            if key == "properties" and isinstance(item, dict):
                normalized[key] = {
                    property_name: normalize(property_schema, resolving)
                    for property_name, property_schema in item.items()
                }
            else:
                normalized[key] = normalize(item, resolving)
        return normalized

    return normalize(raw_schema)


async def call_with_structured_output(
    client,
    prompt: str,
    schema_cls: type[BaseModel],
    max_retries: int = 1,
    server_retries: int = 2,
    base_delay: float = 0.5,
    model: str | None = None,
) -> BaseModel:
    """Call Flash-Lite for structured JSON.

    Retry arguments remain accepted for caller compatibility, but this helper
    makes exactly one credential attempt. The provider key pool owns transport
    failover and schema repair so one logical operation never reuses a slot.
    """
    del max_retries, server_retries, base_delay
    response = await _generate_once(
        client,
        prompt,
        schema_cls,
        model=model,
    )
    return schema_cls.model_validate_json(response.text)


def _schema_repair_prompt(
    original_prompt: str,
    previous_response: str,
    error: ValidationError,
) -> str:
    issues: list[str] = []
    for issue in error.errors(
        include_url=False,
        include_context=False,
        include_input=False,
    )[:8]:
        location = ".".join(str(part) for part in issue.get("loc", ())) or "response"
        issues.append(f"- {location}: {issue.get('msg', 'Invalid value')}")
    issue_text = "\n".join(issues) or "- response: Invalid JSON schema"
    response_excerpt = previous_response[:4000]
    return (
        f"{original_prompt}\n\n"
        "The previous response did not satisfy the required JSON schema. "
        "Return one corrected JSON object only.\n"
        f"Validation issues:\n{issue_text}\n"
        f"Previous JSON:\n{response_excerpt}"
    )


async def _generate_once(
    client,
    prompt: str,
    schema_cls: type[BaseModel],
    *,
    model: str | None = None,
):
    """Make one transport attempt; the provider owns key failover."""

    return await client.aio.models.generate_content(
        model=model or STRUCTURED_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": _gemini_response_schema(schema_cls),
            "temperature": 0,
            "max_output_tokens": 2048,
        },
    )

# Registry

The registry module provides decorator-based plugin registration.

Use these decorators for new methods:

- `@register_probe("name")`
- `@register_monitor("name")`
- `@register_attributor("name")`

The pipeline runner calls `create_probe`, `create_monitor`, and
`create_attributor` to instantiate methods from YAML.

::: SafeLens.core.registry

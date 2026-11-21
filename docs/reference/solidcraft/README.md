# SolidCraft version references

Forge keeps one immutable reference directory per qualified SolidCraft target:

```text
docs/reference/solidcraft/
  0.42.0/
  0.43.0/
  <future-version>/
```

The current qualified reference is [0.43.0](0.43.0/SOURCE.md).
The previous [0.42.0](0.42.0/SOURCE.md) snapshot remains immutable historical
qualification evidence.

## Adding a new SolidCraft version

Before Forge compatibility code is changed for a newer SolidCraft release:

1. keep every existing version directory unchanged;
2. add a sibling directory named for the exact SolidCraft version;
3. add `SOURCE.md` with the exact upstream release and commit;
4. capture the command/reference material and version-specific contract gaps
   needed by Forge;
5. review those differences before adapting Forge;
6. only then update the tested SolidCraft version and qualify the new target.

Do not update the existing version directory in place. Version-to-version
changes must remain reviewable as a new tree.

The repository-level development procedure is documented in
[../../development.md](../../development.md).

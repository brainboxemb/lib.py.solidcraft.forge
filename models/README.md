# Models

A model directory is the physical ownership boundary. CI selects model ids, not engine implementations.

Each model owns one `ci.yml`, one `model.yml`, implementation source directories and model-specific verification expectations. `model.yml.purpose` may contain `example`, `verification`, or both.

A multi-engine model declares implementations in its owner `ci.yml`. Engine implementation ids are local to that model and never become sibling model owners.

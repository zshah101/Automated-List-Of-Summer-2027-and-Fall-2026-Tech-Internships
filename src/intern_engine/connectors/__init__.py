"""ATS connectors. Each exposes `fetch(company, session) -> list[Job]`.

Adding a new source = adding one module here with a `fetch` function and
registering it in `pipeline.CONNECTORS`. Nothing else in the system changes.
"""

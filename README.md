# neosuite-template

The reference skeleton for NeoSuite products and engines. It is a small, complete,
working product, **NeoExample** (`neoexample`), plus a generator that turns it into a
new repository with every identifier renamed.

NeoExample shows each layer once:

- **Rust core** for all domain rules: an `Item` with title normalisation and validation,
  slug generation and a `todo → doing → done` state machine. Errors carry stable codes
  (`title_empty`, `title_too_long`, `transition_invalid`, …).
- **PyO3 bindings** that expose the core to Python as the `neoexample_core` wheel.
- **FastAPI backend** that does HTTP only: a router factory, RFC 9457 problem documents
  with the core's codes, a Server-Sent Events stream, NeoFlow action invocation with
  `Idempotency-Key` and `dry_run`, and the runtime surface (`/healthz`, `/readyz`,
  `/metrics`, `/.well-known/neosuite/manifest.json`).
- **Client module** for the neosuite-app shell: routes, widgets and NeoMind context,
  built on the adaptive `@neospacetech/neosuite-ui` primitives.
- **Contracts**: the object type, event and action schemas and the OpenAPI document,
  with tests that keep the running service in step with them.

## Layout

```text
├── engine/                 Rust workspace
│   ├── core/               neoexample-core: pure logic and unit tests
│   └── py/                 neoexample-py: PyO3 bindings → wheel `neoexample_core`
├── backend/                FastAPI service, package `neoexample` (src layout)
├── frontend/               @neospacetech/neoexample-ui (source-only TS package)
├── contracts/              types/ events/ actions/ api/openapi.yaml
├── deploy/                 Dockerfile.backend, compose.yaml fragment
├── scripts/new_product.py  generator
├── neosuite.toml           component descriptor
└── .github/workflows/      CI: Rust, backend, image, frontend
```

## Run it

Requirements: Rust (stable), Python 3.12+, Node 22.

```sh
python -m venv .venv && . .venv/bin/activate
pip install "maturin>=1.9,<2"

# Rust core
(cd engine && cargo fmt --all --check && cargo clippy --workspace --all-targets -- -D warnings && cargo test --workspace)

# Build the extension into the venv, then the backend
maturin develop -m engine/py/Cargo.toml
pip install -e "backend[dev]"
(cd backend && ruff check . && ruff format --check . && mypy && pytest)

# Serve
uvicorn neoexample.app:app --reload
curl -s localhost:8000/api/v1/items/validate -H 'content-type: application/json' -d '{"title":"  Plan   the launch "}'
curl -N "localhost:8000/api/v1/items/lifecycle?title=Ship"
```

Settings come from `NEOEXAMPLE_*` environment variables (see
`backend/src/neoexample/settings.py`).

The frontend depends on `neosuite-commons` by path, so check that repository out next
to this one:

```sh
cd frontend && npm ci && npm run typecheck
```

Container:

```sh
docker build -f deploy/Dockerfile.backend -t neoexample-backend .
docker run --rm -p 8000:8000 neoexample-backend
```

## Create a product

```sh
python scripts/new_product.py neotasks --title NeoTasks --kind product --dest ../neotasks
python scripts/new_product.py neostore --title NeoStore --kind engine --no-frontend --dest ../neostore
```

The generator copies the template, renames `neoexample` / `NeoExample` / `NEOEXAMPLE`
everywhere (crates, modules, packages, environment prefix, contract and file names) and
writes `neosuite.toml`, `README.md` and `CHANGELOG.md` for the new component. The result
builds and passes its tests as is; replace the `Item` domain from there.

It never overwrites files. Stamping into an existing repository keeps its `LICENSE` and
sets the package metadata to match; otherwise pass `--license-file`. NeoSuite products
and engines are AGPL-3.0-only, while their `contracts/` are Apache-2.0.

## Licence

Apache-2.0. See [LICENSE](LICENSE).

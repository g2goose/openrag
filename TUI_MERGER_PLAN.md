# TUI Merger Plan

## Executive Summary

The BT1-Forge platform currently ships two separate Textual-based TUI applications:

1. **OpenRAG TUI** (`openrag/src/tui/`) — Container management, flow configuration, and document ingestion for the RAG platform. Shipped as a standalone package with its own `docker-compose` lifecycle.
2. **BT1ZAR CLI TUI** (`bt1zar_bt1_CLI/`) — Interactive agent execution, plan review, and IPC server management for the multi-agent runtime.

The merger goal is a single `bt1zar-ui-core` package providing shared UI primitives that both apps consume, reducing duplication and enabling a unified operator experience.

---

## Shared Widget Candidates

The following UI components appear in both apps and are candidates for extraction:

| Widget | OpenRAG TUI | BT1ZAR CLI TUI | Notes |
|--------|-------------|----------------|-------|
| Status bar | `screens/monitor.py` | `main.py` | Service health indicators |
| Log viewer | `screens/logs.py` | Agent output panel | Scrollable log stream with tail/pause |
| Modal base class | `widgets/*.py` (5+ modals) | Confirmation dialogs | Dismiss-on-escape, focus trap |
| Data table | `screens/diagnostics.py` | Plan viewer | Sortable, filterable rows |
| Error notification | `widgets/error_notification.py` | Error overlays | Consistent error UX |
| Progress indicator | `screens/monitor.py` | Streaming progress | Indeterminate + determinate modes |

---

## Proposed Package Structure

```
bt1zar_bt1_CLI/
└── ui_core/                    # New: bt1zar-ui-core package
    ├── pyproject.toml          # Package: bt1zar-ui-core
    ├── __init__.py
    ├── widgets/
    │   ├── __init__.py
    │   ├── status_bar.py       # Service health status bar
    │   ├── log_viewer.py       # Scrollable streaming log viewer
    │   ├── modal_base.py       # Base modal with dismiss/focus-trap
    │   ├── data_table.py       # Sortable data table
    │   └── error_notification.py  # Error overlay widget
    ├── screens/
    │   ├── __init__.py
    │   └── base_screen.py      # Base screen with common keybindings
    └── theme.py                # Shared CSS variables (colors, spacing)
```

Both apps add `bt1zar-ui-core` as a workspace dependency:

```toml
# openrag/pyproject.toml
[tool.uv.sources]
bt1zar-ui-core = { path = "../bt1zar_bt1_CLI/ui_core" }

# bt1zar_bt1_CLI/pyproject.toml (root workspace)
[tool.uv.workspace]
members = ["core", "cli", "smolagents", "ui_core"]
```

---

## Migration Order

### Phase 1 — Extract shared widgets (1–2 days)
1. Create `bt1zar_bt1_CLI/ui_core/` scaffold with `pyproject.toml`
2. Extract `ModalBase` from OpenRAG's `widgets/*.py` modal classes
3. Extract `LogViewer` from OpenRAG's `screens/logs.py`
4. Extract `StatusBar` from OpenRAG's `screens/monitor.py`
5. Write unit tests for each widget using `pytest-textual-snapshot`

### Phase 2 — Wire OpenRAG TUI to ui_core (1 day)
1. Add `bt1zar-ui-core` dependency to `openrag/pyproject.toml`
2. Replace OpenRAG modal classes with `ModalBase` subclasses from ui_core
3. Replace `LogViewer` and `StatusBar` implementations with ui_core versions
4. Run full OpenRAG TUI smoke test (`make dev-cpu`)

### Phase 3 — Wire BT1ZAR CLI TUI to ui_core (1 day)
1. Add `bt1zar-ui-core` to CLI's workspace
2. Replace CLI TUI components with ui_core equivalents
3. Run CLI integration tests (`make test`)

### Phase 4 — Unify theme (0.5 days)
1. Consolidate CSS variables from both apps into `ui_core/theme.py`
2. Apply consistent color palette and spacing to both apps

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenRAG TUI is shipped standalone (pip-installable) | High | ui_core must be publishable to PyPI or bundled into openrag's wheel |
| BT1ZAR CLI TUI may not exist yet as a formal module | Medium | Start with OpenRAG migration only; add CLI integration when TUI exists |
| Textual version drift between apps | Medium | Pin `textual>=0.65.0` in ui_core; both apps inherit the constraint |
| Widget API instability during extraction | Low | Keep widget API minimal (just display + reactive props); no business logic |

---

## Success Criteria

- [ ] `bt1zar-ui-core` package installable via `uv add bt1zar-ui-core`
- [ ] OpenRAG TUI passes full smoke test using ui_core widgets
- [ ] Zero duplicated modal/log-viewer code between apps
- [ ] `pytest-textual-snapshot` tests for each shared widget
- [ ] Both apps render identically to pre-merger baseline

---

*Drafted: 2026-02-20 as part of v2.4.0 cleanup.*

"""Windows UI Automation helpers for driving native DAZ Studio dialogs that
have no working headless scripting equivalent (Bug-Katalog #22 Teil 2:
``DzWearablesAssetFilter.doSave()`` fails with an unexplained generic error
under every configuration tried; the real "File > Save As > Wearable(s)
Preset" GUI action + its two native dialogs work reliably, so this module
drives *those* instead of the broken script API).

Windows-only (``pywinauto``/``pywin32``). Requires the DAZ Studio process to
be running on the same machine as this MCP server process — there is no
remote-UI-automation path.

All findings here were confirmed live (2026-09-09) against DAZ Studio 6.25,
round-tripped end to end against a real figure with a fitted test prop, then
fully cleaned up. See ``docs/daz-mcp-bridge-bugs.md`` #22 for the full
investigation, including approaches that looked reasonable but did not work.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from fastmcp.exceptions import ToolError

try:
    import win32api
    import win32con
    import win32gui
    import win32process
    import win32com.client
    from pywinauto.application import Application

    _PYWINAUTO_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only on non-Windows/no-pywinauto envs
    _PYWINAUTO_AVAILABLE = False


def _require_pywinauto() -> None:
    if not _PYWINAUTO_AVAILABLE:
        raise ToolError(
            "This tool requires pywinauto/pywin32 (Windows-only UI automation) "
            "and a DAZ Studio process running on the same machine as this MCP "
            "server — there is no remote-UI-automation path. Install with "
            "`uv sync` (pywinauto is declared as a Windows-only dependency in "
            "pyproject.toml)."
        )


def find_daz_studio_pid() -> int:
    """Find the running DAZStudio.exe process ID via WMI (no extra dependency
    beyond pywin32, which pywinauto already requires)."""
    _require_pywinauto()
    wmi = win32com.client.GetObject("winmgmts:")
    for proc in wmi.InstancesOf("Win32_Process"):
        if proc.Name == "DAZStudio.exe":
            return proc.ProcessId
    raise ToolError("DAZStudio.exe process not found — is DAZ Studio running on this machine?")


def _find_window(
    pid: int,
    title_predicate: Callable[[str, str], bool],
    timeout: float,
    poll_interval: float = 0.4,
) -> int:
    """Poll for a visible top-level window owned by ``pid`` whose (title,
    class_name) satisfies ``title_predicate``. Returns its hwnd.

    Polling (not a single check) because the DazScript-side action trigger
    runs asynchronously — the window can take a moment to appear after the
    action fires.
    """
    deadline = time.monotonic() + timeout
    matches: list[int] = []

    def cb(hwnd: int, _):
        try:
            _, wpid = win32process.GetWindowThreadProcessId(hwnd)
        except Exception:  # pragma: no cover - defensive, matches prior live testing
            return True
        if wpid == pid and win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            if title_predicate(title, cls):
                matches.append(hwnd)
        return True

    while time.monotonic() < deadline:
        matches.clear()
        win32gui.EnumWindows(cb, None)
        if matches:
            return matches[0]
        time.sleep(poll_interval)
    raise ToolError(
        f"Timed out after {timeout}s waiting for the expected DAZ Studio dialog window."
    )


def _wait_until_closed(hwnd: int, timeout: float, poll_interval: float = 0.3) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not win32gui.IsWindow(hwnd):
            return
        time.sleep(poll_interval)
    raise ToolError(
        f"Dialog (hwnd={hwnd}) did not close within {timeout}s after confirming it."
    )


def _set_native_filename_field(hwnd: int, auto_id: str, text: str) -> None:
    """Set the filename field on a native Windows "Filtered Save" (Explorer-
    style, class ``#32770``) common dialog.

    Confirmed live: this field's ``window_text()``/classic ``WM_GETTEXT``
    always return only the static label ("Dateiname:"), never the real
    value — checking success that way is a trap. The real value must be set
    *and read back* via pywinauto's UIA ``ValuePattern``
    (``set_edit_text()`` / ``get_value()``). Plain ``win32gui.SendMessage(...,
    WM_SETTEXT, ...)`` on the inner Edit HWND does **not** work — this is a
    modern ``IFileDialog``-based common dialog (Vista+), which ignores that
    classic message entirely.
    """
    app = Application(backend="uia").connect(handle=hwnd)
    win = app.window(handle=hwnd)
    edit = win.child_window(auto_id=auto_id, control_type="Edit")
    edit.set_edit_text(text)
    actual = edit.get_value()
    if actual != text:
        raise ToolError(
            f"Failed to reliably set the filename field (got {actual!r}, expected {text!r})."
        )


def _click_native_dialog_button(hwnd: int, control_id: int) -> None:
    """Trigger a button on a native "Filtered Save" common dialog.

    Confirmed live: neither pywinauto's UIA ``Invoke()`` pattern nor a raw
    ``BM_CLICK`` sent to the button's own HWND actually triggers the Save
    action on this dialog — both return without error but leave the dialog
    open. What works: ``WM_COMMAND``/``BN_CLICKED``
    (``wParam = MAKELONG(control_id, 0)``) sent to the **dialog window
    itself**, not the button. ``lParam`` (conventionally the control's HWND)
    was confirmed unnecessary — 0 works.
    """
    wparam = win32api.MAKELONG(control_id, 0)
    win32gui.SendMessage(hwnd, win32con.WM_COMMAND, wparam, 0)


def _invoke_qt_button(hwnd: int, auto_id: str) -> None:
    """Click a button on a DAZ Studio-native Qt6 dialog (as opposed to a
    native Windows common dialog). Confirmed live: unlike the native
    "Filtered Save" dialog's buttons, these respond normally to UIA
    ``Invoke()`` — no WM_COMMAND workaround needed here.
    """
    app = Application(backend="uia").connect(handle=hwnd)
    win = app.window(handle=hwnd)
    btn = win.child_window(auto_id=auto_id, control_type="Button")
    btn.invoke()


# Auto_id prefix for every control on the "Wearable(s) Preset Save Options"
# dialog, confirmed live 2026-09-09.
_WEARABLES_DLG = "App.WearablesAssetFilterDialog"
_WEARABLES_ACCEPT_BTN = f"{_WEARABLES_DLG}.BasicDlgButtonGrpBox.BasicDlgAcceptDialogBtn"
_WEARABLES_CANCEL_BTN = f"{_WEARABLES_DLG}.BasicDlgButtonGrpBox.BasicDlgCancelDialogBtn"


def drive_wearable_preset_save(output_path: str, dialog_timeout: float = 30.0) -> dict:
    """Drive the two native dialogs behind "File > Save As > Wearable(s)
    Preset" to completion, once the DazScript side has already selected the
    target figure and triggered ``DzWearablesAssetFilterAction``.

    Must be called from a worker thread (all pywinauto/win32 calls here are
    blocking) — see ``daz_save_wearable_preset``'s ``asyncio.to_thread`` use.

    Bundles **every currently fitted/parented item on the selected figure**
    into the preset — this is the dialog's own default behavior (its node
    checklist has no confirmed UIA toggle mechanism; see module docstring's
    referenced bug entry) and was not overridden. Callers who only want a
    specific item bundled should ensure nothing else is fitted to the figure
    first.
    """
    _require_pywinauto()
    pid = find_daz_studio_pid()

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    save_hwnd = _find_window(
        pid, lambda title, cls: title == "Filtered Save" and cls == "#32770", dialog_timeout
    )
    _set_native_filename_field(save_hwnd, "1001", str(out))
    _click_native_dialog_button(save_hwnd, 1)  # "&Speichern" / Save

    options_hwnd = _find_window(
        pid, lambda title, _cls: title == "Wearable(s) Preset Save Options", dialog_timeout
    )
    _invoke_qt_button(options_hwnd, _WEARABLES_ACCEPT_BTN)
    _wait_until_closed(options_hwnd, dialog_timeout)

    # DAZ Studio finishes writing the file a moment after the dialog visually
    # closes — confirmed live: an immediate one-shot exists() check raced the
    # write and false-negatived on a file that appeared correctly a fraction
    # of a second later. Poll briefly instead of trusting dialog-closed as
    # "file fully written".
    write_deadline = time.monotonic() + min(dialog_timeout, 10.0)
    while not out.exists() and time.monotonic() < write_deadline:
        time.sleep(0.2)
    if not out.exists():
        raise ToolError(
            f"Save dialog sequence completed but the expected output file was not "
            f"found: {out}"
        )
    return {"success": True, "outputPath": str(out)}

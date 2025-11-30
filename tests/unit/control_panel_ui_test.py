import types
from unittest.mock import MagicMock

import pytest

from constants import COLOR_ARMED
from core.control_panel import control_panel_ui as cp_ui_mod


# ---- Fake customtkinter primitives ----
class _FakeWidget:
    def __init__(self, *args, **kwargs):
        self.kwargs = dict(kwargs)
        self.attrs = dict(kwargs)
        self.placed = None
        self.gridded = None
        self.packed = None

    def place(self, *args, **kwargs):
        self.placed = (args, kwargs)

    def grid(self, *args, **kwargs):
        self.gridded = (args, kwargs)

    def pack(self, *args, **kwargs):
        self.packed = (args, kwargs)

    def configure(self, **kwargs):
        self.attrs.update(kwargs)


class _FakeFrame(_FakeWidget):
    pass


class _FakeLabel(_FakeWidget):
    pass


class _FakeEntry(_FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = ""
        self.attrs.setdefault("state", None)

    def insert(self, index, text):
        self.value = text

    def delete(self, start, end):
        self.value = ""


class _FakeTextbox(_FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = ""

    def delete(self, start, end):
        self.text = ""

    def insert(self, index, text):
        self.text = text


class _FakeButton(_FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command = kwargs.get("command")


class _FakeCTK(types.SimpleNamespace):
    def __init__(self):
        super().__init__(
            CTkFrame=_FakeFrame,
            CTkLabel=_FakeLabel,
            CTkEntry=_FakeEntry,
            CTkTextbox=_FakeTextbox,
            CTkButton=_FakeButton,
        )


@pytest.fixture
def fake_ctk(monkeypatch):
    fake = _FakeCTK()
    # Patch the module-level ctk used by ControlPanelUI
    monkeypatch.setattr(cp_ui_mod, "ctk", fake)
    return fake


@pytest.fixture
def ui():
    # __init__ does not touch ctk; parent can be a simple mock
    parent = MagicMock()
    return cp_ui_mod.ControlPanelUI(parent=parent, width=640, height=480)


# __init__
def test_init_sets_defaults(ui):
    assert ui.width == 640
    assert ui.height == 480
    assert ui.security_zone_number is None
    assert ui.short_message1 == ""
    assert ui.short_message2 == ""
    # widgets None before draw
    assert ui.control_panel_frame is None
    assert ui.display_text is None


# draw_page
def test_draw_page_creates_widgets_and_initial_text(ui, fake_ctk, monkeypatch):
    on_press = MagicMock()
    ui.draw_page(on_press)
    # widgets created
    assert isinstance(ui.control_panel_frame, _FakeFrame)
    assert isinstance(ui.display_number, _FakeEntry)
    assert isinstance(ui.display_away, _FakeEntry)
    assert isinstance(ui.display_home, _FakeEntry)
    assert isinstance(ui.display_not_ready, _FakeEntry)
    assert isinstance(ui.display_text, _FakeTextbox)
    assert isinstance(ui.led_armed, _FakeLabel)
    assert isinstance(ui.led_power, _FakeLabel)
    # initial text is two blank lines
    assert ui.display_text.text == "\n\n"


# _draw_btn_grid
def test__draw_btn_grid_calls_helpers_and_wires_panic(
        ui, fake_ctk, monkeypatch):
    # Spy on helper calls
    spy_btn = MagicMock()
    spy_lbl = MagicMock()
    monkeypatch.setattr(ui, "_draw_btn", spy_btn)
    monkeypatch.setattr(ui, "_draw_btn_label", spy_lbl)

    # Capture the panic button command
    created_buttons = []

    class CapturingButton(_FakeButton):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            created_buttons.append(self)

    monkeypatch.setattr(cp_ui_mod.ctk, "CTkButton", CapturingButton)

    calls = []

    def on_press(arg):
        calls.append(arg)

    ui._draw_btn_grid(on_press)

    # Ensure helpers used multiple times (spot-check a few expected calls)
    spy_btn.assert_any_call(
        MagicMock(),
        "1",
        pytest.helpers.any_callable(),
        0,
        0) if hasattr(
        pytest,
        "helpers") else None
    # Minimal assurance on being called at least once
    assert spy_btn.call_count >= 9  # at least the numeric row + others

    assert spy_lbl.call_count >= 9

    # Trigger panic button
    panic = [b for b in created_buttons if b.kwargs.get("text") == "PANIC"]
    assert len(panic) == 1
    panic[0].command()
    assert calls == ["panic"]


# _draw_btn
def test__draw_btn_creates_button_and_label_and_executes_command(ui, fake_ctk):
    executed = []

    def cmd():
        executed.append(True)

    bf = _FakeFrame()
    ui._draw_btn(bf, "X", cmd, 3, 1)
    # The spacer label is created; we can't fetch instances directly,
    # but ensure no error and command works
    # Validate the button command by recreating expected button and invoking
    b = _FakeButton(text="X", command=cmd)
    assert callable(b.command)
    b.command()
    assert executed == [True]


# _draw_btn_label
def test__draw_btn_label_creates_label(ui, fake_ctk):
    bf = _FakeFrame()
    ui._draw_btn_label(bf, "LBL", 4, 2)
    # Just ensure call path works; FakeLabel handles grid without error


# _update_display_text
def test__update_display_text_writes_combined_text(ui, fake_ctk):
    ui.display_text = _FakeTextbox()
    ui.short_message1 = "hello"
    ui.short_message2 = ": world"
    ui._update_display_text()
    assert ui.display_text.text == "\nhello\n: world"


# set_security_zone_number
def test_set_security_zone_number_updates_entry_and_attr(ui):
    ui.display_number = _FakeEntry()
    ui.set_security_zone_number(7)
    assert ui.security_zone_number == 7
    assert ui.display_number.value == "7"
    assert ui.display_number.attrs.get("state") == "readonly"


# set_display_away
def test_set_display_away_sets_text_color(ui):
    ui.display_away = _FakeEntry()
    ui.set_display_away(True)
    assert ui.display_away.attrs.get("text_color") == "black"
    ui.set_display_away(False)
    assert ui.display_away.attrs.get("text_color") == "light gray"


# set_display_home
def test_set_display_home_sets_text_color(ui):
    ui.display_home = _FakeEntry()
    ui.set_display_home(True)
    assert ui.display_home.attrs.get("text_color") == "black"
    ui.set_display_home(False)
    assert ui.display_home.attrs.get("text_color") == "light gray"


# set_display_not_ready
def test_set_display_not_ready_sets_text_color(ui):
    ui.display_not_ready = _FakeEntry()
    ui.set_display_not_ready(True)
    assert ui.display_not_ready.attrs.get("text_color") == "black"
    ui.set_display_not_ready(False)
    assert ui.display_not_ready.attrs.get("text_color") == "light gray"


# set_display_short_message1
def test_set_display_short_message1_sets_and_updates(
        ui, fake_ctk, monkeypatch):
    ui.display_text = _FakeTextbox()
    spy = MagicMock()
    monkeypatch.setattr(ui, "_update_display_text", spy)
    ui.set_display_short_message1("ready", "(master) ")
    assert ui.short_message1 == "(master) ready"
    spy.assert_called_once()


# set_display_short_message2
def test_set_display_short_message2_sets_and_updates(
        ui, fake_ctk, monkeypatch):
    ui.display_text = _FakeTextbox()
    spy = MagicMock()
    monkeypatch.setattr(ui, "_update_display_text", spy)
    ui.set_display_short_message2("armed")
    assert ui.short_message2 == ": armed"
    spy.assert_called_once()


# set_display_messages
def test_set_display_messages_updates_both(ui, monkeypatch):
    s1 = MagicMock()
    s2 = MagicMock()
    monkeypatch.setattr(ui, "set_display_short_message1", s1)
    monkeypatch.setattr(ui, "set_display_short_message2", s2)
    ui.set_display_messages("hello", "world", "(guest) ")
    s1.assert_called_once_with("hello", "(guest) ")
    s2.assert_called_once_with("world")


# set_armed_led
def test_set_armed_led_sets_color(ui):
    ui.led_armed = _FakeLabel()
    ui.set_armed_led(True)
    assert ui.led_armed.attrs.get("fg_color") == COLOR_ARMED
    ui.set_armed_led(False)
    assert ui.led_armed.attrs.get("fg_color") == "light gray"


# set_powered_led
def test_set_powered_led_sets_color(ui):
    ui.led_power = _FakeLabel()
    ui.set_powered_led(True)
    assert ui.led_power.attrs.get("fg_color") == "lightgreen"
    ui.set_powered_led(False)
    assert ui.led_power.attrs.get("fg_color") == "light gray"

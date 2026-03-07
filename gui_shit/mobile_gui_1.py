import gi
gi.require_version('Gtk', '3.0') 
from datetime import datetime
from gi.repository import Gtk, Gdk, GLib, Pango

import re
import os
import subprocess
from gi.repository import Gio
from gi.repository import GdkPixbuf
import subprocess
from dataclasses import dataclass

screen = Gdk.Screen.get_default()
provider = Gtk.CssProvider()
provider.load_from_path("/home/kips/Desktop/kips_files/gui_shit/style.css")
#provider.load_from_path("C:\\msys64\\home\\jljme\\styles.css")
Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

#os.path.dirname(os.path.abspath(__file__))

ROWS, COLS = 3, 4
PAGE_SIZE = ROWS * COLS

value = 1
wifi_val = 0
vol_value = 0

css_file = "/home/kips/Desktop/kips_files/gui_shit/style.css,"
dynamic_provider = Gtk.CssProvider()


@dataclass
class AppEntry:
    app_id: str                         # e.g. "calc_app"
    title: str                          # e.g. "calculator"
    icon_path: str                      # Path to icon

    stack_name: str                     # The name of the page in the content stack
    is_open: bool = False               # Is the page open?
    #content_page: Gtk.Widget = None    
    nav_widget: Gtk.Widget = None       # Where the created icon is stored
    

"""
App Launcher logic:

if app.is_open

else
    create new GtkEventBox and GtkImage
    store entry in appentry
    pack_start icon ino nav_bar box
    set is_open of he app to true
self.content_stack.set_visible_child_name(app.stack_name)
"""

class Launcher(Gtk.Application):

    def __init__(self):
        super().__init__(application_id="com.example.Launcher")
        self.builder = None
        self.window = None
        self.stack = None
        self.pager_box = None
        self.clock_label = None
        self.temp_label = None
        self.humidity_label = None
        self.nav_bar = None
        self.apps = []  # list of dicts: {"name": "Calculator", "icon": "accessories-calculator"}
        self.open_apps = []

    test_app = AppEntry(
        app_id="test_app",
        title="Test App",
        icon_path="/home/kips/Desktop/kips_files/gui_shit/calculator_128x128.png",
        stack_name="app_stack"
    )

    test_app1 = AppEntry(
        app_id="test_app1",
        title="Test App 1",
        icon_path="/home/kips/Desktop/kips_files/gui_shit/calculator_128x128.png",
        stack_name="status_page"
    )

    open_apps = [test_app, test_app1]

    status_app = AppEntry(
        app_id="status_app",
        title="Status",
        icon_path="/home/kips/Desktop/kips_files/gui_shit/calculator_128x128.png",
        stack_name="status_page"
    )

    apps_app = AppEntry(
        app_id="apps_app",
        title="Apps",
        icon_path="/home/kips/Desktop/kips_files/gui_shit/calculator_128x128.png",
        stack_name="app_stack"
    )

    clock_app = AppEntry(
        app_id="clock_app",
        title="Clock",
        icon_path="/home/kips/Desktop/kips_files/gui_shit/calculator_128x128.png",
        stack_name="clock_fullscreen"
    )

    settings_app = AppEntry(
        app_id="settings_app",
        title="Settings",
        icon_path="/home/kips/Desktop/kips_files/gui_shit/calculator_128x128.png",
        stack_name="settings_page"
    )

    radio_app = AppEntry(
        app_id="radio_app",
        title="Radio",
        icon_path="/home/kips/Desktop/kips_files/gui_shit/calculator_128x128.png",
        stack_name="radio_page"
    )




    def _set_image_scaled(self, image_widget, file_path, size_px=28):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            file_path, 
            width=size_px, 
            height=size_px,
            preserve_aspect_ratio=True
        )
        image_widget.set_from_pixbuf(pixbuf)

    def _update_battery_val(self):
        global value
        #print(f'battery_value: {value}')
        if value < 100:
            value += 1
        else:
            value = 1
        self._update_battery_icon(value, False)  # example values

        return(value)
    
    def _update_wifi_val(self, verbose=False):
        def signal_info():
            signal = subprocess.run(["iw", "dev", "wlan0", "link"],
                capture_output=True,
                text=True,
                check=True
            )
            
            full_str = signal.stdout
            
            strength = full_str.strip().split("\t")[5].strip().split(": ")[1].split(" dBm")[0]

            if verbose:
                name = full_str.strip().split("\t")[1].strip().split(": ")[1]
                print(f'Name: {name}')
                return strength, name
            #print(f'Strength: {strength}')
            return int(strength)
        
        
        try:    
            output = signal_info()
            self._update_wifi_icon(output)
        except:
            self._update_wifi_icon(-1000)
        return True

    def _update_volume_val(self):
        def mute_test():
            mute = subprocess.run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
                capture_output=True,
                text=True,
                check=True
            )
            return mute.stdout.strip().endswith("yes")
        
        def vol_test():
            vol = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True,
                text=True,
                check=True
            )
            
            #print(vol.stdout.strip().split("/")[1].strip().replace("%", ""))
            #return vol.stdout
            return int(vol.stdout.strip().split("/")[1].strip().replace("%", ""))
        
        mute = mute_test()
        
        if mute:
            self._update_volume_icon(0)
            return True
        else:
            self._update_volume_icon(vol_test())
            return True

    def _update_clock(self):
        if self.clock_label is None:
            return False
        now = datetime.now()

        time_str = now.strftime("%H:%M")
        #print(time_str)
        self.clock_label.set_text(time_str)
        self.clock_app_label.set_text(time_str)
        return True

    def _update_volume_icon(self, level):
        if self.volume_icon is None:
            return False     
        if level >= 75:
            icon_name = "volume_4.png"
        elif level >= 50:
            icon_name = "volume_3.png"
        elif level >= 25:
            icon_name = "volume_2.png"
        elif level > 0:
            icon_name = "volume_1.png"
        else:
            icon_name = "volume_0.png"

        self._set_image_scaled(self.volume_icon, icon_name, size_px=28)

    def _update_wifi_icon(self, strength):
        if self.wifi_icon is None:
            return False      
        if strength >= -39:
            icon_name = "wifi_4.png"
        elif strength >= -55:
            icon_name = "wifi_3.png"
        elif strength >= -70:
            icon_name = "wifi_2.png"
        elif strength >= -80:
            icon_name = "wifi_1.png"
        else:
            icon_name = "wifi_0.png"

        self._set_image_scaled(self.wifi_icon, icon_name, size_px=28)

    def _update_battery_icon(self, percentage, is_charging):
        if self.battery_icon is None:
            #print('false')
            return False      
        if is_charging:
            icon_name = "battery_charging.png"
        elif percentage <= 10:
            icon_name = "battery_9.png"
        elif percentage <= 20:
            icon_name = "battery_8.png"
        elif percentage <= 30:
            icon_name = "battery_7.png"
        elif percentage <= 40:
            icon_name = "battery_6.png"
        elif percentage <= 50:
            icon_name = "battery_5.png"
        elif percentage <= 60:
            icon_name = "battery_4.png"
        elif percentage <= 70:
            icon_name = "battery_3.png"
        elif percentage <= 80:
            icon_name = "battery_2.png"
        elif percentage <= 90:
            icon_name = "battery_1.png"
        else:
            icon_name = "battery_0.png"

        self._set_image_scaled(self.battery_icon, icon_name, size_px=100)

    def _build_pages(self):
        chunks = [self.apps[i:i+PAGE_SIZE] for i in range(0, len(self.apps), PAGE_SIZE)] or [[]]

        for child in list(self.stack.get_children()):
            self.stack.remove(child)
        
        for idx, chunk in enumerate(chunks):
            page = self._make_page(chunk)
            self.stack.add_named(page, f"page-{idx}")
        
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(250)
        self.stack.set_visible_child_name("page-0")

        self._rebuild_dots(len(chunks))
        self._rebuild_nav_bar(len(chunks))
        self.stack.show_all()

    def do_activate(self):
        from pathlib import Path

        BASE_DIR = Path(__file__).resolve().parent
        GLADE_FILE = BASE_DIR / "mobile_mode_gui.glade"
        self.BASE_DIR = BASE_DIR
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file(str(GLADE_FILE))

        win = self.builder.get_object("main_window") or self._first_of_type(Gtk.Window)
        self.window = win
        self.content_stack = self.builder.get_object("content_stack")
        self.stack = self.builder.get_object("appStack") or self._first_of_type(Gtk.Stack)
        self.pager_box = self.builder.get_object("pager_box") or self._ensure_pager_box()
        self.clock_label = self.builder.get_object("clock_label")
        self.battery_icon = self.builder.get_object("battery_icon")
        self.wifi_icon = self.builder.get_object("wifi_icon")
        self.volume_icon = self.builder.get_object("volume_icon")
        self.temp_label = self.builder.get_object("temp_label")
        self.humidity_label = self.builder.get_object("humidity")
        self.nav_bar = self.builder.get_object("nav_bar")
        self.home_icon_eb = self.builder.get_object("home_icon_eb")
        self.status_button = self.builder.get_object("status_button")
        self.apps_button = self.builder.get_object("apps_button")
        self.clock_button = self.builder.get_object("clock_button")
        self.shell_stack = self.builder.get_object("shell_stack")
        self.clock_exit_button = self.builder.get_object("clock_exit_button")
        self.clock_app_label = self.builder.get_object("clock_app_label")
        self.settings_button = self.builder.get_object("settings_button")
        self.radio_button = self.builder.get_object("radio_button")
        self.button = self.builder.get_object("Color")

        self.button.connect("color-set", self.on_color_chosen)
        
        self.brightness = self.builder.get_object("brightness")
        self.background_image = self.builder.get_object("background_image")
        self.background_image.connect("file-set", self.on_background_file)
        self.font = self.builder.get_object("Font")
        self.font.connect("font-set", self.on_font)
       
       

        if self.home_icon_eb is not None:
            self.home_icon_eb.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            self.home_icon_eb.connect("button-press-event", self._on_home_icon_clicked)

        if self.status_button is not None:
            self.status_button.connect("clicked", self._on_app_icon_clicked, self.status_app)
        
        if self.apps_button is not None:
            self.apps_button.connect("clicked", self._on_app_icon_clicked, self.apps_app)  # example, replace with actual app entry

        if self.settings_button is not None:
            self.settings_button.connect("clicked", self._on_app_icon_clicked, self.settings_app) 
        
        if self.radio_button is not None:
            self.radio_button.connect("clicked", self._on_app_icon_clicked, self.radio_app)
        
        if self.clock_button is not None:
            self.clock_button.connect("clicked", self._on_clock_button_clicked)  

        if self.clock_exit_button is not None:
            self.clock_exit_button.connect("clicked", self._on_clock_exit_button_clicked)  # example, replace with actual app entry
        
        self.add_window(win)

        #win.fullscreen()
        win.show_all()

        # If your .glade left a single FlowBox in the Stack, remove it; we create pages dynamically.
        for child in list(self.stack.get_children()):
            self.stack.remove(child)

        # sample data; replace with your registry
        '''self.apps = [
            {"name": "calculator_128x128.png", "icon_path": os.path.join(BASE_DIR, "calculator_128x128.png")},
            {"name": "test.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "CALC2.png", "icon_path": os.path.join(BASE_DIR, "CALC2.png")},
            {"name": "CALCULATOR.jpeg", "icon_path": os.path.join(BASE_DIR, "CALCULATOR.jpeg")},
            {"name": "CALCULATOR.png", "icon_path": os.path.join(BASE_DIR, "CALCULATOR.png")},

            {"name": "Test1",   "icon": "utilities-terminal"},
            {"name": "calculator_128x128.png", "icon_path": os.path.join(BASE_DIR, "calculator_128x128.png")},
            {"name": "calculator_128x128.png", "icon_path": os.path.join(BASE_DIR, "calculator_128x128.png")},
            {"name": "test4",   "icon": "utilities-terminal"},
            {"name": "test5",      "icon": "system-file-manager"},
            {"name": "calculator_128x128.png", "icon_path": os.path.join(BASE_DIR, "calculator_128x128.png")},
            {"name": "calculator_128x128.png", "icon_path": os.path.join(BASE_DIR, "calculator_128x128.png")},
            {"name": "test8", "icon": "accessories-calculator"},
            {"name": "test9",   "icon": "utilities-terminal"},
            {"name": "test10",   "icon": "utilities-terminal"},
            {"name": "test11",      "icon": "system-file-manager"},
            {"name": "test12", "icon": "accessories-calculator"},
            {"name": "test13",   "icon": "utilities-terminal"},

            # ... add more
        ]'''

        self.apps = [
            {"name": "calculator", "exec": "galculator", 
            "icon_path": os.path.join(BASE_DIR, "calculator_128x128.png")},
            {"name": "glade", "exec": "glade",
            "icon_path": os.path.join(BASE_DIR, "glade_icon.png")},
            {"name": "app_test3.png", "icon_path": os.path.join(BASE_DIR, "calculator_128x128.png")},
            {"name": "app_test4.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test5.png", "icon_path": os.path.join(BASE_DIR, "calculator_128x128.png")},
            {"name": "app_test6.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test7.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test8.png", "icon_path": os.path.join(BASE_DIR, "test.svg")},
            {"name": "app_test9.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test10.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test11.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test12.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test13.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test14.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test15.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test16.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test17.png", "icon_path": os.path.join(BASE_DIR, "calculator_128x128.png")},
            {"name": "app_test18.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test19.png", "icon_path": os.path.join(BASE_DIR, "calculator_128x128.png")},
            {"name": "app_test20.png", "icon_path": os.path.join(BASE_DIR, "test.png")},
            {"name": "app_test21.png", "icon_path": os.path.join(BASE_DIR, "calculator_128x128.png")},
                        
            # ... add more
        ]

        self._build_pages()

        # Enable swipes/wheel paging and sync dots
        self._enable_paging_gestures(self.stack)
        self.stack.connect("notify::visible-child", self._on_page_changed)

        self._update_clock()
     
        GLib.timeout_add_seconds(1, self._update_clock)
        GLib.timeout_add_seconds(1, self._update_battery_val)
        GLib.timeout_add_seconds(1, self._update_volume_val)  # example values
        GLib.timeout_add_seconds(1, self._update_wifi_val)  # example values

        win.set_application(self)
        win.show_all()

    # ---------- UI helpers ----------
    def _first_of_type(self, klass):
        # fallback if you forgot to set IDs
        for obj in self.builder.get_objects():
            if isinstance(obj, klass):
                return obj
        return None

    def _ensure_pager_box(self):
        # As a last resort, make one and pack at bottom of top-level box.
        top_box = self._first_of_type(Gtk.Box)
        pager = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        pager.set_halign(Gtk.Align.CENTER)
        top_box.pack_end(pager, False, False, 6)
        return pager

    # ---------- A. Paging gestures ----------
    def _enable_paging_gestures(self, widget):
        widget.add_events(Gdk.EventMask.SCROLL_MASK)
        widget.connect("scroll-event", self._on_scroll)
        try:
            from gi.repository import Gtk as Gtk3
            swipe = Gtk3.GestureSwipe.new(widget)
            swipe.connect("swipe", self._on_swipe)
        except Exception:
            pass

    def _on_scroll(self, _w, event):
        if event.direction in (Gdk.ScrollDirection.RIGHT, Gdk.ScrollDirection.DOWN):
            self.goto_next_page()
        elif event.direction in (Gdk.ScrollDirection.LEFT, Gdk.ScrollDirection.UP):
            self.goto_prev_page()
        return True

    def _on_swipe(self, _gesture, vel_x, _vel_y):
        if vel_x < 0:
            self.goto_next_page()
        elif vel_x > 0:
            self.goto_prev_page()



    def goto_next_page(self):
        children = self.stack.get_children()
        if not children: 
            return
        i = self._current_index()
        if i < len(children) - 1:
            self.stack.set_visible_child(children[i+1])

    def goto_prev_page(self):
        pages = self.stack.get_children()
        if not pages: return
        i = self._current_index()
        self.stack.set_visible_child(pages[max(i-1, 0)])

    def _current_index(self):
        child = self.stack.get_visible_child()
        if child is None:
            return 0
        name = self.stack.get_visible_child_name()
        if name and name.startswith("page-"):
            try:
                return int(name.split("-", 1)[1])
            except ValueError:
                pass
        children = self.stack.get_children()
        try: 
            return children.index(child)
        except ValueError:
            return 0

    # ---------- B. Dynamic pages ----------
    def rebuild_pages(self):
        # clear existing pages
        for child in list(self.stack.get_children()):
            self.stack.remove(child)

        chunks = [self.apps[i:i+PAGE_SIZE] for i in range(0, len(self.apps), PAGE_SIZE)] or [[]]
        for idx, chunk in enumerate(chunks):
            page = self._make_page(chunk)
            self.stack.add_named(page, f"page-{idx}")

        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(250)
        self.stack.set_visible_child_name("page-0")

        self._rebuild_dots(len(chunks))
        self._rebuild_nav_bar(len(chunks))
        self.stack.show_all()

    def _make_page(self, app_chunk):
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_max_children_per_line(COLS)
        flow.set_min_children_per_line(COLS)
        flow.set_row_spacing(8)
        flow.set_column_spacing(8)
        flow.set_valign(Gtk.Align.FILL)
        flow.set_halign(Gtk.Align.FILL)

        for app in app_chunk:
            flow.add(self._make_app_tile(app))

        for _ in range(PAGE_SIZE - len(app_chunk)):
            flow.add(self._make_spacer_tile())

        return flow

    def _make_app_tile(self, app):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        icon_widget = None

        icon_file = app.get("icon_path")
        
        if icon_file and os.path.isfile(icon_file):
            icon_widget = Gtk.Image.new_from_file(app["icon_path"])
        else:
            icon_name = app.get("name") or app.get("icon") or "application-x-executable"
            icon_widget = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        
        lbl = Gtk.Label(label=app.get("name","App"))
        lbl.set_max_width_chars(10)
        lbl.set_ellipsize(3)  # PANGO_ELLIPSIZE_END=3
        
        box.pack_start(icon_widget, True, True, 0)
        box.pack_start(lbl, False, False, 0)

        eb = Gtk.EventBox(); eb.add(box)
        eb.connect("button-press-event", lambda *_: self.launch_app(app))
        return eb

    def _make_spacer_tile(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.set_sensitive(False)
        return box

    def launch_app(self, app):
        
        # TODO ensure that apps launch only once and prevent further launches
        
        cmd = app.get("exec")
        if cmd:
            print("Launching:", app["name"])
            subprocess.Popen([cmd])
        else:
            print("No execution path found for", app["name"])
            
        # This was an alternate solution. Worth looking into for potential changes
        # info = Gio.DesktopAppInfo.new("org.gnome.Calculator.desktop")
        # info.launch([], None) 
        
        # TODO further hook into launch mechanism 

    # ---------- C. Dots ----------
    def _rebuild_dots(self, num_pages):
        for child in list(self.pager_box.get_children()):
            self.pager_box.remove(child)

        for i in range(num_pages):
            dot = Gtk.Button(label="●" if i == 0 else "○")
            dot.set_name("pager-dot")
            dot.set_relief(Gtk.ReliefStyle.NONE)
            dot.set_focus_on_click(False)
            dot.set_can_focus(False)
            
            dot.set_margin_left(3)
            dot.set_margin_right(3)

            #dot.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            dot.connect("button-press-event", self._on_dot_clicked, i)

            self.pager_box.pack_start(dot, False, False, 3)
        self.pager_box.show_all()

    def _on_dot_clicked(self, _widget, _event, index):
        children = self.stack.get_children()
        if not children: 
            return
        index = max(0, min(index, len(children)-1))
        self.stack.set_visible_child(children[index])
        
        self._on_page_changed(1)

    def _on_page_changed(self, *_):
        idx = self._current_index()
        for i, child in enumerate(self.pager_box.get_children()):
            if isinstance(child, Gtk.Button):
                child.set_label("●" if i == idx else "○")
                
    ##################################################################################
    # ---------- D. Nav_Bar ----------
    
    def _unique_open_apps(self):
        """Return open apps with duplicates removed, preserving first-seen order."""
        seen = set()
        unique = []
        for app in self.open_apps:
            if app.app_id in seen:
                continue
            seen.add(app.app_id)
            unique.append(app)
        return unique
    
    def _make_nav_widget_for_app(self, app_entry):
        """
        Creates the nav widget ONCE and stores it in app_entry.nav_widget.
        For now: dot button.
        Later: swap the label for an image (icon_path) without changing callers.
        """
        if app_entry.nav_widget is not None:
            return app_entry.nav_widget

        btn = Gtk.Button()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_focus_on_click(False)
        btn.set_can_focus(False)
        btn.set_margin_left(3)
        btn.set_margin_right(3)

        # ---- CURRENT BEHAVIOR: dot ----
        # btn.set_label("●")  # label will be updated by _refresh_nav_active_state()

        # ---- LATER UPGRADE: icon/image ----
        # Uncomment this when you're ready to switch from dot -> image:
        if app_entry.icon_path and os.path.isfile(app_entry.icon_path):
            img = Gtk.Image.new_from_file(app_entry.icon_path)
        else:
            img = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DND)
        btn.set_label("")     # remove dot
        btn.add(img)          # show icon
        btn.show_all()

        btn.get_style_context().add_class("nav-icon")

        # IMPORTANT: your file has an _on_nav_icon_clicked that takes (widget,event,app_entry)
        btn.connect("button-press-event", self._on_nav_icon_clicked, app_entry)

        app_entry.nav_widget = btn
        return btn

    def _refresh_nav_active_state(self):
        """Applies active/inactive styling (and dot fill) based on current stack page."""
        current = self.content_stack.get_visible_child_name()

        for app in self._unique_open_apps():
            w = app.nav_widget
            if not w:
                continue

            is_active = (app.stack_name == current)
            ctx = w.get_style_context()

            # Dot mode: filled dot for active, empty for inactive
            if w.get_label() is not None and w.get_label() != "":
                w.set_label("●" if is_active else "○")

            if is_active:
                ctx.add_class("nav-icon-active")
            else:
                ctx.remove_class("nav-icon-active")

    def _rebuild_nav_bar(self, *_):
        # Clear nav_bar
        for child in list(self.nav_bar.get_children()):
            self.nav_bar.remove(child)

        # Rebuild exactly one nav widget per app
        for app in self._unique_open_apps():
            w = self._make_nav_widget_for_app(app)
            self.nav_bar.pack_start(w, False, False, 3)

        self.nav_bar.show_all()
        self._refresh_nav_active_state()

    def _on_nav_icon_clicked(self, _widget, _event, app_entry):
        self.content_stack.set_visible_child_name(app_entry.stack_name)
        children = self.content_stack.get_children()
        if not children: 
            return
        for child in children:
            if child.get_name() == app_entry.stack_name:
                self.content_stack.set_visible_child(child)
                break
        
        self._on_nav_page_changed(1)

    def _on_nav_page_changed(self, *_):
        idx = self._current_index()
        #for i, child in enumerate(self.nav_bar.get_children()):
        #    if isinstance(child, Gtk.Button):
        #        child.set_label("●" if i == idx else "○")
    
    ###############################################################################                
                
    def goto_next_content_page(self):
        children = self.content_stack.get_children()
        if not children:
            return
        current = self.content_stack.get_visible_child()
        try:
            idx = children.index(current)
        except ValueError:
            return 
        next_idx = (idx + 1) % len(children)
        print(children[next_idx])
        self.content_stack.set_visible_child(children[next_idx])
    
    def _on_home_icon_clicked(self, _widget, _event):
        # SWAP TO: 
        self.content_stack.set_visible_child_name("home_stack")
        return True
   
    def on_color_changed(widget):
        rgba = widget.get_rgba()
        print("Live color:", regba.to_string())
   

    """
    def _on_nav_icon_2_clicked(self, _widget, _event):
        self.content_stack.set_visible_child_name("status_page")    
    
    def _on_nav_icon_3_clicked(self, _widget, _event):
        self.content_stack.set_visible_child_name("app_stack")
    """

    def _on_app_icon_clicked(self, button, app_entry):
        print("Main icon clicked")
        self.open_apps.append(app_entry)
        self._rebuild_nav_bar(len(self.open_apps))
        self.content_stack.set_visible_child_name(f"{app_entry.stack_name}")

            
    def _on_status_button_clicked(self, button):
        print("Status button clicked")
        self.connect("button-press-event", self._on_nav_icon_clicked, self.status_app)
        self.content_stack.set_visible_child_name("status_stack")

    def _on_apps_button_clicked(self, button):
        print("Apps button clicked")
        self.content_stack.set_visible_child_name("app_stack")
        
    def _on_clock_button_clicked(self, button):
        print("Clock button clicked")
        self.shell_stack.set_visible_child_name("clock_fullscreen")

    def _on_clock_exit_button_clicked(self, button):
        print("Clock exit button clicked")
        self.shell_stack.set_visible_child_name("main_shell")

    def _on_settings_button_clicked(self, button):
        print("Settings button clicked")
        self.content_stack.set_visible_child_name("settings_page")
        
    def on_button_clicked(self,widget):
        print("Color Settings button clicked")
        self.popover.popup()
        
    def on_color_chosen(self,widget):
       
        rgba = widget.get_rgba()
        
        hex_color = "#{:02x}{:02x}{:02x}".format(
        int(rgba.red*255),
        int(rgba.green*255),
        int(rgba.blue*255)
        
        
        )
        
        
        print("Selected HEX", hex_color)
        
        #color_str = f"rgb({red}, {green}, {blue})"
        
        css = f"""
        #main_window
            {{
                    background-image : none;
                    background-color: {hex_color};
                
            
        }}
        """
        dynamic_provider.load_from_data(css.encode())

    def on_font(self,widget):
       
        fontupdate = widget.get_font()
        desc = Pango.FontDescription.from_string(fontupdate)
        
        family = desc.get_family()
        size = int(desc.get_size()/ Pango.SCALE)
        weight = int(desc.get_weight())
        style = "italic" if desc.get_style() == Pango.Style.ITALIC else "normal"

        
        #font-style: {style};
        #                    font-weight: {int(weight)};
        
        
        
        css = f"""
        #main_window
            {{
                    
                    font-family: "{family}";
                    font-size: "{size}"px;
                    
                    
                
            
        }}
        """
        data = css.encode("utf-8")
        dynamic_provider.load_from_data(css.encode())

    def on_background_file(self,widget):
        filepath = widget.get_filename()
        
        if filepath:
            css = f"""
            #main_window
            {{
                    background-image : url('{filepath}');
                    background-repeat: no-repeat; 
                    background-position: center; 
                    background-size: cover; 
                
            
            }}
            """
        dynamic_provider.load_from_data(css.encode())
    
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        dynamic_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    
if __name__ == "__main__":

    Launcher().run([])
    


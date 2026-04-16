import os
import sys
import serial

DIRR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIRR)

os.environ["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"
os.environ["GDK_BACKEND"] = "wayland"

import gi
gi.require_version('Gtk', '3.0') 
gi.require_version('WebKit2', '4.1') 
from datetime import datetime
from gi.repository import Gtk, Gdk, GLib, Pango, WebKit2

import re
import subprocess
from gi.repository import Gio
from gi.repository import GdkPixbuf
import subprocess
from dataclasses import dataclass
from esp_sensor_call import call_data
import math
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

path = os.path.join(BASE_DIR, "styles.css")
print(f"Loading CSS from: {path}")

screen = Gdk.Screen.get_default()
provider = Gtk.CssProvider()
dynamic_provider = Gtk.CssProvider()

provider.load_from_path(path)
Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
ROWS, COLS = 3, 4
PAGE_SIZE = ROWS * COLS

value = 1
wifi_val = 0
vol_value = 0


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
        self.camera_proc = None
        self.current_radio_mode = "FM"
        self.apps = []  # list of dicts: {"name": "Calculator", "icon": "accessories-calculator"}
        self.open_apps = []
        
        # Controller Board on Pi UART4
        self.ctrl_ser = None
        self.cursor_x = 0
        self.cursor_y = 0
        self.controller_deadzone = 250
        
        self.app_defaults = {
            "color": "#002f00",
            "image": "",
            "font_family": "Sans",
            "font_size": "14"

            }
        
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            dynamic_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
                       
        #GLib.idle_add(self.setup_browser)
        GLib.idle_add(self.apply_all_styles)

    status_app = AppEntry(
        app_id="status_app",
        title="Status",
        icon_path=os.path.join(BASE_DIR, "icons", "calculator_128x128.png"),
        stack_name="status_page"
    )

    apps_app = AppEntry(
        app_id="apps_app",
        title="Apps",
        icon_path=os.path.join(BASE_DIR, "icons", "battery_1.png"),
        stack_name="app_stack"
    )

    clock_app = AppEntry(
        app_id="clock_app",
        title="Clock",
        icon_path=os.path.join(BASE_DIR, "icons", "volume_1.png"),
        stack_name="clock_fullscreen"
    )

    settings_app = AppEntry(
        app_id="settings_app",
        title="Settings",
        icon_path=os.path.join(BASE_DIR, "icons", "wifi_1.png"),
        stack_name="settings_page"
    )

    radio_app = AppEntry(
        app_id="radio_app",
        title="Radio",
        icon_path=os.path.join(BASE_DIR, "icons", "calculator_128x128.png"),
        stack_name="radio_page"
    )
    
    heartbeat_app = AppEntry(
        app_id="heartbeat_app",
        title="Health",
        icon_path=os.path.join(BASE_DIR, "icons", "calculator_128x128.png"),
        stack_name="heartbeat_page"
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
        try:
            with open("/tmp/batt_capacity", "r") as f:
                contents = f.read().strip()
                percent = contents.split(".0")[0]
                lp = contents.split(".0")[1]
                if lp:
                    lp = True
                #print(lp)
                percent = (int(percent))
                #print(f'percent: {percent}')
                self._update_battery_icon(percent, lp, False)  # example values
                return(percent)
        except FileNotFoundError:
            self._update_battery_icon(-1, False, False)
            print('Battery read error')
            return(-1)
    
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
            icon_name = os.path.join(BASE_DIR, "icons", "volume_4.png")
        elif level >= 50:
            icon_name = os.path.join(BASE_DIR, "icons", "volume_3.png")
        elif level >= 25:
            icon_name = os.path.join(BASE_DIR, "icons", "volume_2.png")
        elif level > 0:
            icon_name = os.path.join(BASE_DIR, "icons", "volume_1.png")
        else:
            icon_name = os.path.join(BASE_DIR, "icons", "volume_0.png")

        self._set_image_scaled(self.volume_icon, icon_name, size_px=28)

    def _update_wifi_icon(self, strength):
        if self.wifi_icon is None:
            return False      
        if strength >= -39:
            icon_name = os.path.join(BASE_DIR, "icons", "wifi_4.png")
        elif strength >= -55:
            icon_name = os.path.join(BASE_DIR, "icons", "wifi_3.png")
        elif strength >= -70:
            icon_name = os.path.join(BASE_DIR, "icons", "wifi_2.png")
        elif strength >= -80:
            icon_name = os.path.join(BASE_DIR, "icons", "wifi_1.png")
        else:
            icon_name = os.path.join(BASE_DIR, "icons", "wifi_0.png")

        self._set_image_scaled(self.wifi_icon, icon_name, size_px=28)

    def _update_battery_icon(self, percentage, low_power=False, is_charging = False):
        if self.battery_icon is None:
            #print('false')
            return False
        if low_power:
            icon_name = icon_path=os.path.join(BASE_DIR, "icons", "wifi_0.png")
        elif is_charging:
            icon_name = icon_path=os.path.join(BASE_DIR, "icons", "battery_charging.png")
        elif percentage <= 10.0:
            icon_name = icon_path=os.path.join(BASE_DIR, "icons", "battery_9.png")
        elif percentage <= 20.0:
            icon_name = icon_path=os.path.join(BASE_DIR, "icons", "battery_8.png")
        elif percentage <= 30.0:
            icon_name = icon_path=os.path.join(BASE_DIR, "icons", "battery_7.png")
        elif percentage <= 40.0:
            icon_name = icon_path=os.path.join(BASE_DIR, "icons", "battery_6.png")
        elif percentage <= 50.0:
            icon_name = icon_path=os.path.join(BASE_DIR, "icons", "battery_5.png")
        elif percentage <= 60.0:
            icon_name = icon_path=os.path.join(BASE_DIR, "icons", "battery_4.png")
        elif percentage <= 70.0:
            icon_name = icon_path=os.path.join(BASE_DIR, "icons", "battery_3.png")
        elif percentage <= 80.0:
            icon_name = icon_path=os.path.join(BASE_DIR, "icons", "battery_2.png")
        elif percentage <= 90.0:
            icon_name = icon_path=os.path.join(BASE_DIR, "icons", "battery_1.png")
        else:
            icon_name = icon_path=os.path.join(BASE_DIR, "icons", "battery_0.png")

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
        self.temp_output_stack = self.builder.get_object("temp_output_stack")
        self.humidity_label = self.builder.get_object("humidity_label")
        self.humidity_output_stack = self.builder.get_object("humidity_output_stack")
        #self.brightness_label = self.builder.get_object("brightness_label")
        #self.brightness_output_stack = self.builder.get_object("brightness_output_stack")
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
        self.heartbeat_button = self.builder.get_object("heartbeat_button")
        self.background_color_button = self.builder.get_object("background_color")
        self.autobrightness_toggle = self.builder.get_object("autobrightness_switch")
        self.manual_brightness_tab = self.builder.get_object("manual_brightness_tab")
        self.browser_exit_button = self.builder.get_object("browser_exit_button")
        
        self.background_color_button.connect("color-set", self.on_color_chosen)
        
        self.brightness = self.builder.get_object("brightness")
        self.background_image = self.builder.get_object("background_image")
        self.background_image.connect("file-set", self.on_background_file)
        self.font = self.builder.get_object("Font")
        self.font.connect("font-set", self.on_font)
        
        self.setup_volume_controls()
        
        self.browser_page = self.builder.get_object("browser_page")
        # self.setup_browser()
        self.browser_button = self.builder.get_object("browser")
        #self.browser_button.connect("clicked", self.browser_open)
        self.brightness_slider = self.builder.get_object("brightness")
        self.brightness_slider.connect("value-changed" , self.on_brightness)
        self.font_color_select = self.builder.get_object("font_color")
        self.font_color_select.connect("color-set", self.on_font_color_chosen)
        self.backlight_path  ="/sys/class/backlight/10-0045/brightness"
        #radio buttons
        self.radio_freq_display = self.builder.get_object("radio_freq_display")
        self.radio_mode_label = self.builder.get_object("radio_mode_label")
        self.radio_meta_label = self.builder.get_object("radio_meta_label")
        self.seek_down_button = self.builder.get_object("seek_down_button")
        self.seek_up_button = self.builder.get_object("seek_up_button")
        self.step_down_button = self.builder.get_object("step_down_button")
        self.step_up_button = self.builder.get_object("step_up_button")
        self.status_radio_button = self.builder.get_object("status_radio_button")
        self.radio_status_label = self.builder.get_object("radio_status_label")
                
        
        #Additional radio set up
        self.am_fm_button = self.builder.get_object("AM_FM_Button")
        self.manual_radio_input = self.builder.get_object("manual_radio_input")
        
        if self.am_fm_button:
            self.am_fm_button.set_label(f"{self.current_radio_mode}")
            self.am_fm_button.connect("clicked", self.am_fm_toggle)
           
        #Triggers when user presses "enter" in textbox
        if self.manual_radio_input:
            self.manual_radio_input.connect("activate", self.freq_entered)
        
        self.radio_enter = self.builder.get_object("radio_enter")
        
        if self.radio_enter:
            self.radio_enter.connect("clicked", self.freq_entered)
        if self.radio_freq_display:
            self.radio_freq_display.set_text("89.90 MHz")

        if self.radio_mode_label:
            self.radio_mode_label.set_text("FM")

        if self.radio_meta_label:
            self.radio_meta_label.set_text("Waiting for status...")

        if self.radio_status_label:
            self.radio_status_label.set_text("Radio ready")

        #Sets up main menu buttons on the home screen
        thermometer_gif = os.path.join(BASE_DIR, "icons", "thermometer_64x64.gif")
        self._set_button_media(
            self.status_button,
            thermometer_gif,
            size_px=56,
            button_w=96,
            button_h=96,
            keep_label=True
        )

        apps_gif = os.path.join(BASE_DIR, "icons", "apps_64x64.gif")
        self._set_button_media(
            self.apps_button,
            apps_gif,
            size_px=56,
            button_w=96,
            button_h=96,
            keep_label=True
        )
        
        settings_gif = os.path.join(BASE_DIR, "icons", "gear_64x64.gif")
        self._set_button_media(
            self.settings_button,
            settings_gif,
            size_px=56,
            button_w=96,
            button_h=96,
            keep_label=True
        )        

        radio_gif = os.path.join(BASE_DIR, "icons", "radio_64x64.gif")
        self._set_button_media(
            self.radio_button,
            radio_gif,
            size_px=56,
            button_w=96,
            button_h=96,
            keep_label=True
        )

        heart_gif = os.path.join(BASE_DIR, "icons", "Heart_64x64.gif")
        self._set_button_media(
            self.heartbeat_button,
            heart_gif,
            size_px=56,
            button_w=96,
            button_h=96,
            keep_label=True
        )
        
        clock_gif = os.path.join(BASE_DIR, "icons", "clock_64x64.gif")
        self._set_button_media(
            self.clock_button,
            clock_gif,
            size_px=56,
            button_w=96,
            button_h=96,
            keep_label=True
        )
        

        if self.home_icon_eb is not None:
            self.home_icon_eb.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            self.home_icon_eb.connect("button-press-event", self._on_home_icon_clicked)

        if self.status_button is not None:
            self.status_button.connect("clicked", self._open_status_page)
        
        if self.apps_button is not None:
            self.apps_button.connect("clicked", self._on_app_icon_clicked, self.apps_app)  # example, replace with actual app entry

        if self.settings_button is not None:
            self.settings_button.connect("clicked", self._on_app_icon_clicked, self.settings_app) 
        
        if self.radio_button is not None:
            self.radio_button.connect("clicked", self._on_app_icon_clicked, self.radio_app)
        
        if self.heartbeat_button is not None:
            self.heartbeat_button.connect("clicked", self._on_app_icon_clicked, self.heartbeat_app)
        
        if self.clock_button is not None:
            self.clock_button.connect("clicked", self._on_clock_button_clicked)  

        if self.clock_exit_button is not None:
            self.clock_exit_button.connect("clicked", self._on_exit_button_clicked)  # example, replace with actual app entry
        
        if self.browser_exit_button is not None:
            self.browser_exit_button.connect("clicked", self._on_exit_button_clicked)
        
        if self.autobrightness_toggle is not None:
            self.autobrightness_toggle.connect("notify::active", self._on_brightness_auto)
        
        #radio button activations
            
        if self.seek_down_button:
            self.seek_down_button.connect("clicked", self.seek_down)

        if self.seek_up_button:
            self.seek_up_button.connect("clicked", self.seek_up)

        if self.step_down_button:
            self.step_down_button.connect("clicked", self.step_down)

        if self.step_up_button:
            self.step_up_button.connect("clicked", self.step_up)

        if self.status_radio_button:
            self.status_radio_button.connect("clicked", self.get_status)

        
        #self._update_status_page()
        
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

        #Displays and sets up the applications in the additional apps area
        self.apps = [
            {"name": "Calculator", 
            "type": "external", 
            "exec": "galculator", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "calculator_128x128.png")},
            
            {"name": "Browser", 
            "type": "internal", 
            "handler": "browser_open", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "google.png")},
            
            {"name": "Camera", 
            "type": "internal", 
            "handler" : "camera_toggle",
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "camera_128x1281.png")},
            
            {"name": "app_test5.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "calculator_128x128.png")},
            
            {"name": "app_test6.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test7.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test8.png", 
            "icon_path": os.path.join(BASE_DIR, 
            "icons", "test.png")},
            
            {"name": "app_test9.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test10.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test11.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test12.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test13.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test14.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test15.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test16.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test17.png",
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test18.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test19.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test20.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
            
            {"name": "app_test21.png", 
            "icon_path": os.path.join(BASE_DIR, "icons", 
            "test.png")},
                        
            # ... add more
        ]

        self._build_pages()

        # Enable swipes/wheel paging and sync dots
        self._enable_paging_gestures(self.stack)
        self.stack.connect("notify::visible-child", self._on_page_changed)

        self._update_clock()
     
        GLib.timeout_add_seconds(1, self._update_clock)
        GLib.timeout_add_seconds(1, self._update_battery_val)
        #GLib.timeout_add_seconds(1, self._update_volume_val)  # example values
        GLib.timeout_add_seconds(1, self._update_wifi_val)  # example values
        
        self.setup_controller_serial() 
        GLib.timeout_add(16, self._poll_controller_input)
        
        win.set_application(self)
        win.show_all()

    # ---------- UI helpers ----------
    def _first_of_type(self, klass):
        # fallback if you forgot to set IDs
        for obj in self.builder.get_objects():
            if isinstance(obj, klass):
                return obj
        return None
        
    
    
    
    def setup_controller_serial(self):
        try:
            self.ctrl_ser = serial.Serial("/dev/ttyAMA4", 115200, timeout=0)
            print("Controller UART ready on /dev/ttyAMA4")
        except Exception as e:
            self.ctrl_ser = None
            print(f"Controller UART open failed: {e}")

    def _poll_controller_input(self):
        if self.ctrl_ser is None:
            return True

        try:
            while self.ctrl_ser.in_waiting:
                line = self.ctrl_ser.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    print("CTRL:", line)
                    self._handle_controller_line(line)
        except Exception as e:
            print(f"Controller UART read failed: {e}")

        return True

    def _handle_controller_line(self, line):
        if line.startswith("M,"):
            try:
                _, xs, ys = line.split(",", 2)
                x = int(xs)
                y = int(ys)
                self._handle_controller_motion(x, y)
            except Exception as e:
                print(f"Bad motion packet '{line}': {e}")
            return

        if line == "UP":
            self._controller_focus_move("up")
        elif line == "DOWN":
            self._controller_focus_move("down")
        elif line == "LEFT":
            self._controller_focus_move("left")
        elif line == "RIGHT":
            self._controller_focus_move("right")
        elif line == "ENTER":
            self._controller_activate_focused()

    def _handle_controller_motion(self, x, y):
        if abs(x) < self.controller_deadzone and abs(y) < self.controller_deadzone:
            return

        # For now, treat joystick as directional focus navigation.
        if abs(x) > abs(y):
            if x > 0:
                self._controller_focus_move("right")
            else:
                self._controller_focus_move("left")
        else:
            if y > 0:
                self._controller_focus_move("down")
            else:
                self._controller_focus_move("up")

    def _controller_focus_move(self, direction):
        win = self.window
        if not win:
            return

        current = win.get_focus()
        if current:
            if direction == "up":
                current.child_focus(Gtk.DirectionType.UP)
            elif direction == "down":
                current.child_focus(Gtk.DirectionType.DOWN)
            elif direction == "left":
                current.child_focus(Gtk.DirectionType.LEFT)
            elif direction == "right":
                current.child_focus(Gtk.DirectionType.RIGHT)

    def _controller_activate_focused(self):
        win = self.window
        if not win:
            return

        current = win.get_focus()
        if current and hasattr(current, "activate"):
            try:
                current.activate()
                return
            except Exception:
                pass

        if current and isinstance(current, Gtk.Button):
            current.clicked()
    
    
    

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
    def setup_volume_controls(self):
        self.volumecontrol = self.builder.get_object("Volume")
        self.volumetop = self.builder.get_object("volumetop")
        
        if not self.volumecontrol or not self.volumetop:
            print("volume widgets not found")
            return
            
        self.shared_volume_adjustment = Gtk.Adjustment(
            value=0.5,
            lower=0.0,
            upper=1.0,
            step_increment=0.01,
            page_increment=0.05,
            page_size=0.0
        )
        
        self.volumecontrol.set_adjustment(self.shared_volume_adjustment)
        self.volumetop.set_adjustment(self.shared_volume_adjustment)

        # initialize from real system volume
        init_percent = self.get_system_volume_percent()
        init_value = init_percent / 100.0

        self._updating_volume_ui = True
        self.shared_volume_adjustment.set_value(init_value)
        self._updating_volume_ui = False

        self.update_volume_icons(init_percent)

        # connect both widgets
        self.volumecontrol.connect("value-changed", self.on_volume_changed)
        self.volumetop.connect("value-changed", self.on_volume_changed)

        # poll real system volume so outside changes get reflected
        GLib.timeout_add(500, self.sync_volume_from_system)
        
        
    def sync_volume_from_system(self):
        volume_percent = self.get_system_volume_percent()
        muted = self.is_system_muted()

        if muted:
            volume_percent = 0

        ui_value = self.shared_volume_adjustment.get_value()
        system_value = volume_percent / 100.0

        # only update UI if it actually changed
        if abs(ui_value - system_value) > 0.01:
            self._updating_volume_ui = True
            self.shared_volume_adjustment.set_value(system_value)
            self._updating_volume_ui = False

        self.update_volume_icons(volume_percent)
        self._update_volume_icon(volume_percent)

        return True    
        
    def get_system_volume_percent(self):
        try:
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True,
                text=True,
                check=True
            )

            # Example line:
            # Volume: front-left: 49152 /  75% / -7.50 dB, ...
            matches = re.findall(r'(\d+)%', result.stdout)
            if matches:
                return int(matches[0])

        except Exception as e:
            print(f"Error reading system volume: {e}")

        return 50

    def is_system_muted(self):
        try:
            result = subprocess.run(
                ["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().endswith("yes")
        except Exception as e:
            print(f"Error reading mute state: {e}")
            return False    
        
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
        cmd = app.get("exec")
        handler_name = app.get("handler")
        
        if cmd:
            subprocess.Popen([cmd])
            return
        if handler_name:
            handler = getattr(self, handler_name, None)
            if callable(handler):
                handler(None)
            else:
                print(f"Handler '{handler_name}' not found")
            return
        print(f"No exec or handler defined for {app.get('name', 'unknown app')}")
            
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
            
            dot.set_margin_start(3)
            dot.set_margin_end(3)

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
        Creates the nav widget ONCE.
        Forces the 64px source into a 32px buffer to keep the header small.
        """
        if app_entry.nav_widget is not None:
            return app_entry.nav_widget

        btn = Gtk.Button()
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_focus_on_click(False)
        btn.set_can_focus(False)
        btn.set_margin_start(3)
        btn.set_margin_end(3)

        if app_entry.icon_path and os.path.isfile(app_entry.icon_path):
            # MINIMAL EDIT: Use at_scale(32, 32)
            # Even if the file is 64px, this creates a 32px snapshot.
            # A 32px image physically cannot force the header to be "massive."
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                app_entry.icon_path, 32, 32, True
            )
            img = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            img = Gtk.Image.new_from_icon_name("application-x-executable", Gtk.IconSize.DND)

        # Ensure the widget itself also reports 32px to the header layout
        img.set_pixel_size(32)
        img.set_size_request(32, 32)

        btn.set_image(img)
        btn.set_always_show_image(True)
        btn.show_all()
        btn.get_style_context().add_class("nav-icon")

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
            # if w.get_label() is not None and w.get_label() != "":
            #    w.set_label("●" if is_active else "○")

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
        #        child.set_label("●" if i == idx else "○")et_label("●" if i == idx else "○")
    
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

    def _make_button_image(self, file_path, size_px=64):
        
        """
        Handles animated GIFs natively.
        Best performance when the source file is already scaled to size_px.
        """
        image = Gtk.Image()

        if not file_path or not os.path.isfile(file_path):
            return image

        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == ".gif":
                # MINIMAL EDIT: Use the native animation loader.
                # This bypasses the math-heavy manual scaling logic.
                anim = GdkPixbuf.PixbufAnimation.new_from_file(file_path)
                image.set_from_animation(anim)
            else:
                # Standard static load
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    file_path, size_px, size_px, True
                )
                image.set_from_pixbuf(pixbuf)

            # Enforce size consistency
            image.set_size_request(size_px, size_px)
            image.set_hexpand(False)
            image.set_vexpand(False)
            image.set_halign(Gtk.Align.CENTER)
            image.set_valign(Gtk.Align.CENTER)

        except Exception as e:
            print(f"Error loading button image '{file_path}': {e}")
            image.set_from_icon_name("image-missing", Gtk.IconSize.BUTTON)

        return image

    def _set_button_media(self, button, file_path, size_px=64, button_w=100, button_h=100, keep_label=True):
        if button is None:
            return

        image = self._make_button_image(file_path, size_px=size_px)

        button.set_image(image)
        button.set_always_show_image(True)
        button.set_image_position(Gtk.PositionType.TOP)

        button.set_size_request(button_w, button_h)
        button.set_hexpand(False)
        button.set_vexpand(False)
        button.set_halign(Gtk.Align.CENTER)
        button.set_valign(Gtk.Align.CENTER)
        button.set_relief(Gtk.ReliefStyle.NONE)

        if not keep_label:
            button.set_label("")
    
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

    def _open_status_page(self, button):
        self._update_status_page()
        self._on_app_icon_clicked(button, self.status_app)
            
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

    def _on_exit_button_clicked(self, button):
        print("Clock exit button clicked")
        self.shell_stack.set_visible_child_name("main_shell")

    def _on_settings_button_clicked(self, button):
        print("Settings button clicked")
        self.content_stack.set_visible_child_name("settings_page")
        
    def _on_brightness_auto(self, switch, _):
        if self.autobrightness_toggle.get_active():
            self.manual_brightness_tab.set_visible_child_name("brightness_cover")
            self.start_auto_brightness()
            # SET TO READ FROM LDR FOR BRIGHTNESS
        else:
            # POLL FROM SLIDER TO DETERMINE BRIGHTNESS VALUE
            self.manual_brightness_tab.set_visible_child_name("manual_brightness")
            self.stop_auto_brightness()
    def start_auto_brightness(self):
        print("Auto brightness started")
    def stop_auto_brightness(self):
        print("Stop auto brightness")
        low1 = 0 #low of slider
        low2 = 6 # bottom bound of screen brightness
        high1 = 100 #where we want to stop scale
        high2 = 74 #max bound of screen brightness before cutoff
        cmd = f'cat {self.backlight_path}'
        hw_val = subprocess.check_output(cmd, shell = True).decode().strip()
        hw_val = int(hw_val)
        if hw_val == 255:
            hw_val = high2
        val = int(((hw_val *(high1 - low1))/(high2-low2)) - low2 +low1)
        #set value of slider to val
        self.on_brightness(self.brightness_slider)
        self.brightness.set_value(val)
    def on_brightness(self,slider):
        val = slider.get_value()
        low1 = 0 #low of slider
        low2 = 6 # bottom bound of screen brightness
        high1 = 100 #where we want to stop scale
        high2 = 74 #max bound of screen brightness before cutoff
        if val <= 89:
            hw_val = low2 + (val- low1) * (high2-low2) /(high1-low1)
        else:
            hw_val = 255
        self.apply_brightness(int(hw_val))
    def apply_brightness (self , level):
          try:
            cmd = f'echo {level} | sudo tee {self.backlight_path}'
            subprocess.run(cmd, shell = True, check = True, capture_output = True)
            
          except Exception as e:
            print(f"brightness error: {e}")
            
            
            
            
            
            
            
            
            
            
            
            
    def _update_status_page(self):
        # Sensor 1
        try:
            s1_temp_str, s1_hum_str = call_data(tempHum=True)
            s1_temp = float(s1_temp_str)
            s1_hum = float(s1_hum_str)

            if math.isnan(s1_temp) or math.isnan(s1_hum):
                raise ValueError("Sensor 1 returned NaN")

            s1_temp_f = (s1_temp * 9 / 5) + 32
            self.temp_label.set_text(f"S1: {s1_temp_f:.1f}°F, {s1_temp:.1f}°C")
            self.humidity_label.set_text(f"S1: {s1_hum:.1f}%")

            if self.temp_output_stack:
                self.temp_output_stack.set_visible_child_name("temp_label")
            if self.humidity_output_stack:
                self.humidity_output_stack.set_visible_child_name("humidity_label")

        except Exception as e:
            print("Error calling sensor 1 data:", e)
            self.temp_label.set_text("S1: Loading...")
            self.humidity_label.set_text("S1: Loading...")

        # Sensor 2
        try:
            s2_temp_str, s2_hum_str = call_data(sensor2=True)
            s2_temp = float(s2_temp_str)
            s2_hum = float(s2_hum_str)

            print(f"S2 temp/humidity: {s2_temp}, {s2_hum}")

            # If you add dedicated Glade labels for sensor 2, update them here.
            # Example:
            # self.temp2_label.set_text(f"S2: {(s2_temp * 9/5) + 32:.1f}°F, {s2_temp:.1f}°C")
            # self.humidity2_label.set_text(f"S2: {s2_hum:.1f}%")

        except Exception as e:
            print("Error calling sensor 2 data:", e)

        # LDR
        try:
            brightness = call_data(lux=True)
            print(f"brightness: {brightness}")

            # If you add a Glade label for brightness, update it here.
            # Example:
            # self.brightness_label.set_text(str(brightness))

        except Exception as e:
            print("Error calling brightness data:", e)
        
        
        
        
        
        
    
    #radio functions 
            
    def send_to_radio_backend(self, command_string):
        print(f"Sending to Radio: {command_string}")

        try:
            result = subprocess.run(
                ["python3", "radio_send.py", command_string],
                capture_output=True,
                text=True
            )

            response = (result.stdout or "").strip()
            err = (result.stderr or "").strip()

            if err:
                print("RADIO ERR:", err)

            if response:
                print("RADIO:", response)
                if self.radio_status_label:
                    self.radio_status_label.set_text(response)
                self._update_radio_display_from_response(response)
            else:
                if self.radio_status_label:
                    self.radio_status_label.set_text("No radio response")

        except Exception as e:
            print(f"Backend Error: {e}")
            if self.radio_status_label:
                self.radio_status_label.set_text(f"Backend Error: {e}")
                
                
                
                
                
                
                
    def freq_entered(self, entry=None):
        if self.manual_radio_input:
            self.manual_radio_input.set_text("")

        if self.radio_status_label:
            self.radio_status_label.set_text("Direct TUNE not supported by current ESP firmware")
            
            
            
            
            
            
    def step_up(self, button=None):
        self.send_to_radio_backend("STEPUP 10")

    def step_down(self, button=None):
        self.send_to_radio_backend("STEPDN 10")

    def seek_up(self, button=None):
        self.send_to_radio_backend("SEEKUP")

    def seek_down(self, button=None):
        self.send_to_radio_backend("SEEKDN")

    def get_status(self, button=None):
        self.send_to_radio_backend("STATUS")
    def am_fm_toggle(self, button):
        if self.current_radio_mode == "FM":
            self.current_radio_mode = "AM"
        else:
            self.current_radio_mode = "FM"

        button.set_label(self.current_radio_mode)
        self.send_to_radio_backend(f"MODE {self.current_radio_mode}")
        self.get_status()
        
        
        
        
        
        
        
        
    def _update_radio_display_from_response(self, response):
        if not response:
            return

        if "MODE FM" in response or response.endswith("FM"):
            self.current_radio_mode = "FM"
            if self.am_fm_button:
                self.am_fm_button.set_label("FM")
            if self.radio_mode_label:
                self.radio_mode_label.set_text("FM")

        elif "MODE AM" in response or response.endswith("AM"):
            self.current_radio_mode = "AM"
            if self.am_fm_button:
                self.am_fm_button.set_label("AM")
            if self.radio_mode_label:
                self.radio_mode_label.set_text("AM")

        if self.radio_meta_label:
            self.radio_meta_label.set_text(response)
            
    
    
    
    
    
    
    
    
    def setup_browser(self):
        if getattr(self, "browser", None) is not None:
            return

        self.browser = WebKit2.WebView()
        self.browser_page.pack_start(self.browser, True, True, 0)
        self.browser_page.show_all()

    def browser_open(self, button=None):
        self.setup_browser()
        print("browser clicked")
        self.browser.load_uri("https://www.google.com")
        self.shell_stack.set_visible_child_name("browser_page")
    #camera
    def camera_toggle(self,widget):
        if self.camera_proc is None:
            try:
                self.camera_proc = subprocess.Popen([
                "rpicam-hello",
                "-t", "0"
                ])
                print("preview started")
            except Exception as e:
                print(f"Failed to launch camera: {e}")
        else:
            self.stop_camera()
    def stop_camera(self):
        if self.camera_proc:
            self.camera_proc.send_signal(signal.SIGINT)
            self.camera_proc.wait()
            self.camera_proc = None
            print("Camera stopped")
    

    #background color
    def on_color_chosen(self,widget):
       
        rgba = widget.get_rgba()
        
        hex_color = "#{:02x}{:02x}{:02x}".format(
        int(rgba.red*255),
        int(rgba.green*255),
        int(rgba.blue*255)
        )
                        
        print("Selected background HEX", hex_color)
        
        self.app_defaults["color"] = hex_color
        
        self.app_defaults["image"] = ""
        
        self.apply_all_styles()
        
    def on_font_color_chosen(self,widget):
       
        rgba = widget.get_rgba()
        
        hex_color = "#{:02x}{:02x}{:02x}".format(
        int(rgba.red*255),
        int(rgba.green*255),
        int(rgba.blue*255)
        )
        
        
        print("Selected font HEX", hex_color)
        
        self.app_defaults["font_color"] = hex_color
        
        self.apply_all_styles()

    def on_font(self,widget):
       
        raw_font = widget.get_font()
        parts = raw_font.split()
        
        self.app_defaults["font_family"] =  "".join(parts[:-1])
        self.app_defaults["font_size"]  = parts[-1]
        
        self.apply_all_styles()

    def on_background_file(self,widget):
        filepath = widget.get_filename()
        
        if filepath:
           self.app_defaults["image"] = filepath
           self.apply_all_styles()
    
    #Volume Functions      
    def set_volume(self, volume_percent):
        try:
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume_percent}%"],
                capture_output=True,
                text=True,
                check=True
            )

            if volume_percent > 0:
                subprocess.run(
                    ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"],
                    capture_output=True,
                    text=True,
                    check=True
                )

        except Exception as e:
            print(f"Hardware Volume Error: {e}")
    
    def get_pi_volume(self):
        
        try:
            result = subprocess.run(
            ["amixer", "get", "Master"],
            capture_output = True, text = True
            )
            
            if "[" in result.stdout:
                val = result.stdout.split("[")[1].split("%")[0]
                return int(val)
                
        except:
            return 50
        return 50
    
    def on_volume_changed (self, widget, value):
        if getattr(self, "_updating_volume_ui", False):
            return
            
        volume_percent = int(round(value *100))
        
        self.set_volume(volume_percent)
        self.update_volume_icons(volume_percent)
        #GLib.idle_add(self.set_volume, volume_percent)
        
    def update_volume_icons(self, volume_percent):
        if volume_percent >= 75:
            icon_name = "volume_4.png"
        elif volume_percent >= 50:
            icon_name = "volume_3.png"
        elif volume_percent >= 25:
            icon_name = "volume_2.png"
        elif volume_percent > 0:
            icon_name = "volume_1.png"
        else:
             icon_name = "volume_0.png"
        
        icon_path = os.path.join(BASE_DIR, "icons", icon_name)

        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                icon_path,
                28,
                28,
                True
            )

            for btn in [self.volumecontrol, self.volumetop]:
                new_icon = Gtk.Image.new_from_pixbuf(pixbuf)
                btn.set_image(new_icon)
                btn.set_always_show_image(True)

        except Exception as e:
            print(f"Error updating volume icons: {e}")
            
    #Radio Functions
    def send_to_radio_backend(self, command_string):
        """
        Sends a string command (e.g., 'MODE FM' or 'TUNE 9550') 
        to the ESP32 serial bridge.
        """
        
        print(f"Sending to Radio: {command_string}")
        
        try:
            # Pass the command string as a single argument to the serial script
            subprocess.Popen(["python3", "radio_send.py", command_string])
        
        except Exception as e:
            print(f"Backend Error: {e}")
    
    def am_fm_toggle(self, button):
        
        #Swaps Modes
        if self.current_radio_mode == "FM":
            self.current_radio_mode = "AM"
            
        else:
            self.current_radio_mode = "FM"
            
        #Updates button text so user can see changes
        button.set_label(self.current_radio_mode)
        
        #Send ESP32 command so it actually switches bands
        self.send_to_radio_backend(f"MODE {self.current_radio_mode}")
        
        
    def freq_entered(self, entry):
        
        if self.manual_radio_input:
            raw_freq = self.manual_radio_input.get_text().strip()
        
        if not raw_freq:
            return

        # Clear textbox after something is entered so user knows its sent
        self.manual_radio_input.set_text("")

        try:
            if self.current_radio_mode == "FM":
                freq_val = int(float(raw_freq) * 100)
            else:
                freq_val = int(raw_freq)

            self.send_to_radio_backend(f"TUNE {freq_val}")
        except ValueError:
            print("Invalid frequency format.")
                
        
    def apply_all_styles(self):
        bg_color = self.app_defaults.get("color", "#002f00")
        font_color = self.app_defaults.get("font_color", "#00ee00") # Default to white
        font_family = self.app_defaults.get("font_family", "sans-serif")
        font_size = self.app_defaults.get("font_size", "12")

        # Style for the main window container
        css_data = f"""
        #main_window {{
            background-color: {bg_color};
            background-repeat: no-repeat; 
            background-position: center; 
            background-size: cover; 
        """

        if self.app_defaults.get("image"):
            css_data += f"background-image: url('{self.app_defaults['image']}');"
        else:
            css_data += "background-image: none;"

        css_data += "}\n"

        # Style for all children (Fonts)
        css_data += f"""
        #main_window * {{
            font-family: "{font_family}", sans-serif;
            font-size: {font_size}px;
            color: {font_color};
        }}
        """
        
        try:
            databytes = css_data.encode("utf-8")
            # For GTK 3, load_from_data ofte
            dynamic_provider.load_from_data(databytes, len(databytes))
        except Exception as e:
            print(f"Css Syntax Error: {e}")
        
   
        
    def on_exit_clicked(self,widget):
        print("Shuting down im out bro")
        sys.exit(0)
    
if __name__ == "__main__":

    Launcher().run([])
    


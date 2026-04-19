#!/bin/bash

# 1. Wait for hardware
sleep 5

# 2. FORCE the correct ID for kipster (1000)
# We don't use variables like $UID here because at boot, $UID is 0.
TARGET_UID=1000
export XDG_RUNTIME_DIR=/run/user/$TARGET_UID

# 3. Create the directory if it's missing (Crucial!)
if [ ! -d "$XDG_RUNTIME_DIR" ]; then
    mkdir -p $XDG_RUNTIME_DIR
    chown kips1:kips1 $XDG_RUNTIME_DIR
    chmod 700 $XDG_RUNTIME_DIR
fi

# 4. Check Power State
STATE=$(python3 /usr/local/bin/power_detect.py)

if [ "$STATE" == "wall" ]; then
    systemctl start lightdm
else
    # 5. Launch as kipster using the HARD-CODED 1000 path
    # Also added WLR_BACKEND=drm to ensure it uses the screen, not another wayland session
    sudo -u kips1 dbus-run-session -- env \
        XDG_RUNTIME_DIR=/run/user/1000 \
        WAYLAND_DISPLAY=wayland-0 \
        GDK_BACKEND=wayland \
        GTK_USE_PORTAL=0 \
        CLUTTER_BACKEND=wayland \
        WLR_BACKEND=drm \
        WLR_NO_HARDWARE_CURSORS=1 \
        labwc -S  "/usr/bin/python3 /home/kips1/Desktop/KIPS-MKII/gui_shit/mobile_gui_1.py"
fi

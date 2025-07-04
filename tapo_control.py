import sys
from PyP100 import PyP100

# Replace with your actual Tapo plug details
TAPO_IP = "192.168.1.241"
TAPO_EMAIL = "rickygreenidge@gmail.com"
TAPO_PASSWORD = "424026GreenGar"

if len(sys.argv) != 2 or sys.argv[1] not in ["on", "off", "status"]:
    print("Usage: python tapo_control.py [on|off|status]")
    sys.exit(1)

action = sys.argv[1]

plug = PyP100.P100(TAPO_IP, TAPO_EMAIL, TAPO_PASSWORD)
plug.handshake()
plug.login()

if action == "on":
    plug.turnOn()
    print("✅ Plug turned ON.")
elif action == "off":
    plug.turnOff()
    print("✅ Plug turned OFF.")
elif action == "status":
    info = plug.getDeviceInfo()
    print(f"🔷 Plug is currently: {'ON' if info['device_on'] else 'OFF'}")

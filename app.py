from flask import Flask, render_template, jsonify, request
import serial
import time

app = Flask(__name__)

# Try to connect to Arduino
try:
    arduino = serial.Serial('COM9', 9600, timeout=1)
    time.sleep(2)  # Give time for Arduino to reset
    print("✅ Connected to Arduino on COM4")
except Exception as e:
    arduino = None
    print(f"❌ Failed to connect to COM4: {e}\n❌ No Arduino found.")

# Global override variable
ai_override = None  # Options: "ON", "OFF", or None for AI control

@app.route('/')
def dashboard():
    return render_template('index.html')  # Make sure index.html is in templates/

@app.route('/data')
def get_data():
    global ai_override

    if arduino:
        try:
            # Only read if data is available
            if arduino.in_waiting > 0:
                line = arduino.readline().decode('utf-8').strip()
                print(f"[DEBUG] Arduino says: {line}")

                if line.startswith("rain:"):
                    parts = line.split(',')
                    rain = int(parts[0].split(':')[1])
                    soil = int(parts[1].split(':')[1])
                    temp = float(parts[2].split(':')[1])
                    hum = float(parts[3].split(':')[1])

                    # AI logic
                    action = "ON" if soil < 40 else "OFF"
                    if ai_override is not None:
                        action = ai_override

                    # Send signal to Arduino
                    arduino.write((action + '\n').encode())

                    return jsonify({
    "rain": rain,
    "soil": soil,
    "temp": temp,
    "hum": hum,
    "action": action,
    "mode": "Manual" if ai_override else "AI"
})


        except Exception as e:
            print("❌ Error reading serial:", e)

    # If nothing available or error occurred
    return jsonify({
        "rain": 0,
        "soil": 0,
        "temp": 0,
        "hum": 0,
        "action": "NO DATA"
    })

@app.route('/control', methods=['POST'])
def control():
    global ai_override
    command = request.json.get('command')

    if command == "ON":
        ai_override = "ON"
        if arduino:
            arduino.write(b'1')
            print("🟢 LED ON (Manual)")
    elif command == "OFF":
        ai_override = "OFF"
        if arduino:
            arduino.write(b'0')
            print("🔴 LED OFF (Manual)")
    else:
        ai_override = None
        print("🔄 AI Reset")

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=False)

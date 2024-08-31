from flask import Flask, jsonify, render_template
import threading
import socket
from datetime import datetime

app = Flask(__name__)

# Global variables to store incoming messages in a structured format
ohlc_data = []
trades_data = []

# Function to handle incoming socket connections
def socket_server():
    global ohlc_data, trades_data
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Bind to the specified address and port
        serversocket.bind(('localhost', 8888))
        print("[Info]\tServer successfully bound to port 8888")

        # Start listening for incoming connections
        serversocket.listen(7000)
        print("[Info]\tServer is now listening for connections")

        # Accept a connection
        connection, addr = serversocket.accept()
        print("[Info]\tConnection established with:", addr)

        msg = ''
        while not "END CONNECTION\0" in msg:
            try:
                # Receive data from the connection
                data = connection.recv(1024)
                if not data:
                    break
                msg = data.decode().strip()
                print("[INFO]\tReceived Message:", msg)

                # Process and store the data
                if "OHLC" in msg:
                    # Split the message into key-value pairs
                    ohlc_values = msg.split(" ")

                    # Debug print to verify the message structure
                    print(f"[DEBUG]\tProcessing OHLC values: {ohlc_values}")

                    if len(ohlc_values) >= 6:
                        try:
                            current_time = datetime.utcnow().isoformat() + 'Z'  # Current UTC time in ISO format
                            ohlc_entry = {
                                "symbol": ohlc_values[0].split(':')[0],
                                "open": float(ohlc_values[2].split('=')[1].replace("\x00", "")),
                                "high": float(ohlc_values[3].split('=')[1].replace("\x00", "")),
                                "low": float(ohlc_values[4].split('=')[1].replace("\x00", "")),
                                "close": float(ohlc_values[5].split('=')[1].replace("\x00", "")),
                                "time": current_time
                            }
                            ohlc_data.append(ohlc_entry)
                            print(f"[INFO]\tOHLC data stored: {ohlc_entry}")
                        except IndexError:
                            print("[ERROR]\tUnexpected format in OHLC data")
                        except ValueError:
                            print("[ERROR]\tInvalid number format in OHLC data")

                elif "Open Trades" in msg:
                    trades = msg.split("\n")[1:]
                    print(f"[DEBUG]\tProcessing Trade values: {trades}")
                    
                    for trade in trades:
                        if trade:
                            trade_values = trade.split(" ")
                            try:
                                trade_entry = {
                                    "ticket": int(trade_values[0].split('=')[1].replace("\x00", "")),
                                    "symbol": trade_values[1].split('=')[1],
                                    "volume": float(trade_values[2].split('=')[1].replace("\x00", "")),
                                    "open_price": float(trade_values[3].split('=')[1].replace("\x00", "")),
                                    "current_price": float(trade_values[4].split('=')[1].replace("\x00", "")),
                                    "time": datetime.utcnow().isoformat() + 'Z'  # Current UTC time in ISO format
                                }
                                trades_data.append(trade_entry)
                                print(f"[INFO]\tTrade data stored: {trade_entry}")
                            except (IndexError, ValueError):
                                print("[ERROR]\tError processing trade data")

            except socket.error as e:
                print("[Error]\tSocket error:", e)
                break

    except socket.error as e:
        print("[Error]\tFailed to bind or listen:", e)

    finally:
        # Close the connection and the server socket
        connection.close()
        serversocket.close()
        print("[Info]\tServer socket closed")

# Start the socket server in a separate thread
threading.Thread(target=socket_server, daemon=True).start()

# Flask endpoint to serve the OHLC data in JSON format
@app.route('/api/v1/data/ohlc', methods=['GET'])
def get_ohlc_data():
    if ohlc_data:
        return jsonify(ohlc_data[-1])  # Return the latest OHLC data
    else:
        print("[ERROR]\tNo OHLC data available")  # Debugging info
        return jsonify({"error": "No OHLC data available"}), 404

# Flask endpoint to serve the Trades data in JSON format
@app.route('/api/v1/data/trades', methods=['GET'])
def get_trades_data():
    if trades_data:
        return jsonify(trades_data)  # Return the latest trades data
    else:
        print("[ERROR]\tNo trades data available")  # Debugging info
        return jsonify({"error": "No trades data available"}), 404

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

import asyncio
import json
import websockets
from datetime import datetime


class WebSocketStreamer:
    """Manages WebSocket streaming and receiving."""

    def __init__(self, port, speed_factor):
        self.port = port
        self.speed_factor = speed_factor
        self.server = None  # will hold server instance

    async def stream_messages(self, websocket, messages):
        """Stream AIS messages over WebSocket."""

        # Sort the list of messages by timestamp (for handling multiple vessels)
        messages.sort(
            key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%dT%H:%M:%S.%f"),
            reverse=True,
        )

        try:
            if self.speed_factor == -1:
                for msg in messages:
                    await websocket.send(json.dumps(msg))
                await websocket.send("__END__")  # signal end of stream
            else:
                interval = 5 * 60 / self.speed_factor
                for msg in messages:
                    await websocket.send(json.dumps(msg))
                    await asyncio.sleep(interval)
                await websocket.send("__END__")
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed by client.")

    async def receive_messages(self, db_manager):
        """Receive and ingest AIS messages from WebSocket."""
        try:
            async with websockets.connect(f"ws://localhost:{self.port}") as websocket:
                while True:
                    message = await websocket.recv()
                    if message == "__END__":
                        print("All messages received. Exiting.")
                        break
                    db_manager.ingest_message(json.loads(message))
        except Exception as e:
            print(f"Error in receiving: {e}")

    async def run(self, messages, db_manager):
        """Run WebSocket server and client, then exit."""
        # Start the server
        self.server = await websockets.serve(
            lambda ws: self.stream_messages(ws, messages), "localhost", self.port
        )
        print(f"WebSocket server running on ws://localhost:{self.port}")

        # Run client
        await self.receive_messages(db_manager)

        # After client finishes, stop the server and shut down
        self.server.close()
        await self.server.wait_closed()
        print("WebSocket server closed. Program exiting.")

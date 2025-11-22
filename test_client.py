"""
Simple test client for Real-Time Podcast AI Assistant.
Simulates text-based transcript for testing without audio.
"""

import asyncio
import json
import websockets
from datetime import datetime


# Sample podcast conversation for testing
SAMPLE_CONVERSATION = [
    "Welcome to today's podcast about artificial intelligence.",
    "We're discussing the latest developments in large language models.",
    "ChatGPT was released by OpenAI in November 2022.",
    "It quickly gained over 100 million users within two months.",
    "That made it the fastest-growing consumer application in history.",
    "The model is based on transformer architecture.",
    "Transformers were introduced in the paper 'Attention is All You Need'.",
    "This was published by Google researchers in 2017.",
    "The architecture revolutionized natural language processing.",
    "Now let's talk about climate change impacts.",
    "Global temperatures have risen by about 1.1 degrees Celsius since pre-industrial times.",
    "The Paris Agreement aims to limit warming to 1.5 degrees Celsius.",
    "Arctic sea ice has been declining at a rate of 13% per decade.",
    "This is one of the most visible signs of climate change.",
    "Many scientists believe we need immediate action.",
]


async def test_transcript_simulation():
    """
    Simulate a podcast by sending text transcripts to the server.
    This is useful for testing without actual audio.
    """
    uri = "ws://localhost:8000/listen"

    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to server\n")

            for i, text in enumerate(SAMPLE_CONVERSATION):
                # Simulate transcript event
                transcript_event = {
                    "type": "transcript",
                    "text": text,
                    "is_final": True,
                    "timestamp": datetime.now().isoformat(),
                }

                print(f"[{i+1}/{len(SAMPLE_CONVERSATION)}] Sending: {text}")

                # Send as text message
                await websocket.send(json.dumps(transcript_event))

                # Receive response
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(), timeout=2.0
                    )
                    response_data = json.loads(response)

                    # Print server response
                    if response_data.get("type") == "topic_update":
                        print(
                            f"  → Topic: {response_data.get('current_topic')} "
                            f"(Total: {response_data.get('total_topics')})"
                        )

                    elif response_data.get("type") == "fact_queued":
                        print(
                            f"  → Fact check queued (Queue: {response_data.get('queue_size')})"
                        )

                except asyncio.TimeoutError:
                    pass

                # Wait between messages
                await asyncio.sleep(1)

            print("\n✓ All messages sent successfully")
            print("\nWaiting 5 seconds for final fact checks...")
            await asyncio.sleep(5)

    except websockets.exceptions.WebSocketException as e:
        print(f"✗ WebSocket error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def test_api_endpoints():
    """Test the REST API endpoints."""
    import aiohttp

    base_url = "http://localhost:8000"

    print("Testing API Endpoints")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        # Test health check
        async with session.get(f"{base_url}/") as resp:
            data = await resp.json()
            print(f"✓ Health Check: {data.get('status')}")

        # Test stats
        async with session.get(f"{base_url}/stats") as resp:
            data = await resp.json()
            print(f"✓ Stats: {data}")

        # Test topics
        async with session.get(f"{base_url}/topics") as resp:
            data = await resp.json()
            print(f"✓ Topics: {data.get('total_topics')} topics found")

        # Test facts
        async with session.get(f"{base_url}/facts") as resp:
            data = await resp.json()
            print(f"✓ Facts: {data.get('total')} fact checks performed")


async def main():
    """Main test runner."""
    print("Real-Time Podcast AI Assistant - Test Client")
    print("=" * 50)
    print()

    # First test API endpoints
    print("1. Testing API Endpoints...")
    try:
        await test_api_endpoints()
    except Exception as e:
        print(f"✗ API test failed: {e}")
        print("Make sure the server is running (python main.py)")
        return

    print()
    print("2. Testing WebSocket Transcript Simulation...")
    await test_transcript_simulation()

    print()
    print("=" * 50)
    print("Testing complete!")
    print()
    print("Check the server logs for detailed processing information.")
    print("Visit http://localhost:8000/facts to see fact-checking results.")


if __name__ == "__main__":
    asyncio.run(main())

import sys
import os
from pathlib import Path
import asyncio
from dotenv import load_dotenv
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

from src.utils.config_loader import load_config
from src.voice_assistant import VoiceCodingAssistant
from src.utils.logger import setup_logger

# Global assistant instance for cleanup
assistant = None

async def shutdown():
    """Cleanup tasks tied to the service's shutdown."""
    global assistant
    if assistant:
        await assistant.stop()
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    
    await asyncio.gather(*tasks, return_exceptions=True)

def handle_exception(loop, context):
    """Handle exceptions outside of coroutines"""
    msg = context.get("exception", context["message"])
    logging.error(f"Caught exception: {msg}")

async def main():
    global assistant
    
    # Initialize logger
    logger = setup_logger()
    logger.info("Starting CodeMe AI Voice Assistant...")

    # Load configuration
    config = load_config()
    
    # Initialize the assistant
    assistant = VoiceCodingAssistant(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        project_root=config["project_root"],
        wake_word=config["wake_word"]
    )
    
    try:
        # Start the assistant
        await assistant.start()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(0.1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        await shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if assistant:
            asyncio.run(shutdown())
        print("Shutdown complete")
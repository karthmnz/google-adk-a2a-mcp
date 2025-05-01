import sys, os
sys.path.append(os.path.join(os.path.dirname(sys.path[0]), ''))
from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from task_manager import AgentTaskManager
from capital_agent import CaptialAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=3092)
def main(host, port):
    try:
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="Captial Agent",
            name="Captial Agent Tool",
            description="Helps finding capitals",
            tags=["capital"],
            examples=["What's the capital of France?"],
        )
        agent_card = AgentCard(
            name="Captial Agent",
            description="Helps finding capitals",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=CaptialAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=CaptialAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=CaptialAgent()),
            host=host,
            port=port,
        )
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()

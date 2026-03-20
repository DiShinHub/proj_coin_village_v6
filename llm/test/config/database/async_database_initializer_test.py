import asyncio
from pathlib import Path

from app.config.database_config.database_config_entities_runner import DatabaseConfigEntitiesRunner
from app.config.database_config.database_config_repository import database_config_repository, Base as RepositoryBase
from app.config.database_config.database_config_runner import DatabaseConfigRunner

database_config_runner = DatabaseConfigRunner(
    database_properties_location=Path("../../../properties/database_properties.yaml"),
    database_properties_local_location=Path("../../../properties/database_properties.yaml.local"),
)
database_config_runner.run(is_async=True, engine_echo=True)
Base = RepositoryBase

get_engine = database_config_repository.get_engine
get_session = database_config_repository.get_session

database_config_entities_runner = DatabaseConfigEntitiesRunner(get_engine())
asyncio.run(database_config_entities_runner.run_async())

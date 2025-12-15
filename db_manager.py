import docker
import time
import os
import psycopg2
from docker.errors import NotFound, APIError

class PostgresManager:
    """
    Manages the lifecycle of a PostgreSQL Docker container for the application.
    
    This class handles checking for existing containers, starting new ones,
    ensuring the database is ready for connections, and cleaning up if necessary.
    """
    def __init__(self, 
                 container_name="memory_agent_postgres", 
                 user=None, 
                 password=None, 
                 db_name=None, 
                 port=5432,
                 data_dir="./pgdata"):
        """
        Initialize the PostgresManager.

        Args:
            container_name (str): Name of the Docker container.
            user (str): Postgres user.
            password (str): Postgres password.
            db_name (str): Name of the database to create/connect to.
            port (int): Port to map the database to on the host.
            data_dir (str): Local directory to bind mount for data persistence.
        """
        self.container_name = container_name
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "postgres")
        self.db_name = db_name or os.getenv("POSTGRES_DB", "customer_memory")
        self.port = port
        # Ensure the data directory path is absolute
        self.data_dir = os.path.abspath(data_dir)
        # Initialize Docker client using environment variable settings
        self.client = docker.from_env()

    def get_safe_db_url(self):
        """Constructs a safe URL for logging (hides password)."""
        return f"postgresql://{self.user}:****@localhost:{self.port}/{self.db_name}"

    def start_container(self):
        """
        Starts the Postgres container if it is not already running.
        
        If the container exists but is stopped, it restarts it.
        If it doesn't exist, it creates a new one with the specified configuration.
        
        Returns:
            str: The database connection URL.
        """
        try:
            # Check if container already exists
            container = self.client.containers.get(self.container_name)
            if container.status != "running":
                print(f"Starting existing container {self.container_name}...")
                container.start()
        except NotFound:
            # Container doesn't exist, create a new one
            print(f"Creating and starting new container {self.container_name}...")
            # Ensure local data directory exists for persistence
            os.makedirs(self.data_dir, exist_ok=True)
            
            self.client.containers.run(
                "postgres:15-alpine",
                name=self.container_name,
                environment={
                    "POSTGRES_USER": self.user,
                    "POSTGRES_PASSWORD": self.password,
                    "POSTGRES_DB": self.db_name
                },
                ports={f"5432/tcp": self.port},
                # Mount local directory to /var/lib/postgresql/data for persistence
                volumes={self.data_dir: {'bind': '/var/lib/postgresql/data', 'mode': 'rw'}},
                detach=True
            )
        
        # Block until the database is making connections
        self._wait_for_db()
        return self._get_db_url()

    def _get_db_url(self):
        """Constructs the SQLAlchemy/Psycopg2 connection URL."""
        return f"postgresql://{self.user}:{self.password}@localhost:{self.port}/{self.db_name}"

    def _wait_for_db(self, retries=10, delay=2):
        """
        Waits for the database to be ready to accept connections.
        
        It attempts to connect repeatedly until successful or retries run out.
        
        Args:
            retries (int): Number of attempts before failing.
            delay (int): Seconds to wait between attempts.
        """
        print("Waiting for database to be ready...")
        url = self._get_db_url()
        for i in range(retries):
            try:
                # Attempt connection
                conn = psycopg2.connect(url)
                conn.close()
                print("Database is ready!")
                return
            except psycopg2.OperationalError:
                # Connection failed, wait and retry
                if i < retries - 1:
                    time.sleep(delay)
                else:
                    raise Exception("Could not connect to the database after multiple retries.")

    def stop_container(self):
        """Stops the Postgres container if it exists."""
        try:
            container = self.client.containers.get(self.container_name)
            container.stop()
            print(f"Container {self.container_name} stopped.")
        except NotFound:
            print(f"Container {self.container_name} not found.")

if __name__ == "__main__":
    # Test execution block
    manager = PostgresManager()
    try:
        url = manager.start_container()
        print(f"DB access URL: {manager.get_safe_db_url()}")
    except Exception as e:
        print(f"Error: {e}")

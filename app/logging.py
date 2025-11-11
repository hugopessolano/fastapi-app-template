import sys, sqlite3, json, atexit
from pathlib import Path
from loguru import logger

from app.config import get_settings

settings = get_settings()
DB_FILE_PATH = Path(settings.resolved_logs_db_path)
DB_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
DB_FILE = str(DB_FILE_PATH)

class SQLiteSink:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._setup_table()
        atexit.register(self.close)

    def _connect(self):
        """Establece la conexión con la base de datos."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            #print(f"Conectado a la base de datos SQLite: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error al conectar con SQLite DB '{self.db_path}': {e}", file=sys.stderr)
            self.conn = None
            self.cursor = None

    def _setup_table(self):
        """Crea la tabla de logs si no existe."""
        if not self.cursor: return
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level_name TEXT NOT NULL,
                    level_no INTEGER NOT NULL,
                    message TEXT,
                    module TEXT,
                    funcName TEXT,
                    line INTEGER,
                    extra TEXT
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error al crear/verificar la tabla 'logs': {e}", file=sys.stderr)

    def write(self, message):
        if not self.conn or not self.cursor:
            print("Saltando log a SQLite: No hay conexión a la base de datos.", file=sys.stderr)
            return
        try:
            # Parsea el registro JSON enviado por Loguru
            record = json.loads(message)['record']

            log_entry = {
                'timestamp': record['time']['repr'],
                'level_name': record['level']['name'],
                'level_no': record['level']['no'],
                'message': record['message'],
                'module': record['module'],
                'funcName': record['function'],
                'line': record['line'],
                'extra': json.dumps(record.get('extra', {}))
            }
            self.cursor.execute("""
                INSERT INTO logs (timestamp, level_name, level_no, message, module, funcName, line, extra)
                VALUES (:timestamp, :level_name, :level_no, :message, :module, :funcName, :line, :extra)
            """, log_entry)
            self.conn.commit()

        except json.JSONDecodeError as e:
            print(f"Error al decodificar el mensaje JSON del log: {e}", file=sys.stderr)
            print(f"Data recibida: {message}", file=sys.stderr)
        except sqlite3.Error as e:
            print(f"Error al escribir log en SQLite DB: {e}", file=sys.stderr)
            # try: self.conn.rollback() except: pass
        except Exception as e:
            print(f"Error inesperado en SQLiteSink: {e}", file=sys.stderr)

    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.conn:
            try:
                self.conn.commit()
                self.conn.close()
                print(f"Conexión SQLite '{self.db_path}' cerrada.")
                self.conn = None
                self.cursor = None
            except sqlite3.Error as e:
                print(f"Error al cerrar la conexión SQLite: {e}", file=sys.stderr)

    def __call__(self, message):
        """Hace que la instancia de la clase sea callable para logger.add."""
        self.write(message)

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    level=settings.logging_stdout_level,
    format="<green>{time:YYYY/MM/DD - HH:mm:ss}</green> <level>{level: <8}</level> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

child_logger = logger.bind()


sqlite_sink = SQLiteSink(DB_FILE)

child_logger.add(
    sqlite_sink,
    serialize=True,
    level=settings.logging_db_level,
    catch=False
)

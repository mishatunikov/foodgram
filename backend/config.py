from dataclasses import dataclass

from environs import Env


@dataclass
class DjangoSettings:
    """Конфигурационные данные для Django."""

    secret_key: str
    debug: bool
    db_prod: bool


@dataclass
class HostSettings:
    """Конфигурационные данные хоста."""

    domain_name: str
    host_ip: str


@dataclass
class PostgreSettings:
    """Конфигурационные данные для СУБД PostgreSQL."""

    db_user: str
    db_password: str
    db_host: str
    db_name: str
    db_port: int


@dataclass
class Config:
    """Конфигурационные данные всего проекта."""

    django_settings: DjangoSettings
    db: PostgreSettings
    host: HostSettings


def load_env() -> Config:
    env = Env()
    env.read_env()
    return Config(
        DjangoSettings(
            secret_key=env.str('SECRET_KEY', 'SECRET_KEY'),
            db_prod=env.bool('DB_PROD'),
            debug=env.bool('DEBUG'),
        ),
        PostgreSettings(
            db_user=env.str('POSTGRES_USER', 'postgres'),
            db_password=env.str('POSTGRES_PASSWORD', ''),
            db_name=env.str('POSGRES_DB', 'postgres'),
            db_host=env.str('DB_HOST', ''),
            db_port=env.int('DB_PORT', 5432),
        ),
        HostSettings(
            domain_name=env.str('DOMAIN_NAME', 'localhost'),
            host_ip=env.str('HOST_IP', '127.0.0.1'),
        ),
    )


config: Config = load_env()

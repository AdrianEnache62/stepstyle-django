CREATE SCHEMA IF NOT EXISTS django;

CREATE USER stepstyle_user WITH ENCRYPTED PASSWORD 'parola_stepstyle';

GRANT ALL ON DATABASE stepstyle_db TO stepstyle_user;
ALTER ROLE stepstyle_user SET search_path = django, public;
GRANT ALL ON SCHEMA django TO stepstyle_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA django TO stepstyle_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA django TO stepstyle_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA django TO stepstyle_user;
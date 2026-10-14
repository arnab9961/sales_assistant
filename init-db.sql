-- Database Initialization Script for Sunset Kuakata AI Sales Operations Assistant
-- Executed automatically on PostgreSQL startup

DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE rolname = 'analytics_ro') THEN
      CREATE ROLE analytics_ro WITH LOGIN PASSWORD 'analytics_ro_password';
   END IF;
END
$do$;

-- Connect and grant read-only privileges
GRANT CONNECT ON DATABASE sales_ops TO analytics_ro;
GRANT USAGE ON SCHEMA public TO analytics_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analytics_ro;

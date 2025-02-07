-- Databricks notebook source
-- MAGIC %python
-- MAGIC import re
-- MAGIC username = spark.sql("SELECT current_user()").first()[0]
-- MAGIC clean_username = re.sub("[^a-zA-Z0-9]", "_", username)
-- MAGIC database = f"dbacademy_{clean_username}_adewd_jobs"
-- MAGIC spark.conf.set("da.database", f"dbacademy_{clean_username}_adewd_jobs")

-- COMMAND ----------

USE ${da.database}

-- COMMAND ----------

-- MAGIC %python
-- MAGIC # TODO
-- MAGIC dbutils.widgets.text("key")
-- MAGIC key = dbutils.widgets.get("key")

-- COMMAND ----------

CREATE TABLE IF NOT EXISTS task_4
(key STRING, run_time TIMESTAMP);

-- COMMAND ----------

-- MAGIC %python
-- MAGIC spark.sql(f"INSERT INTO task_4 VALUES ('From {key}', current_timestamp())")

-- COMMAND ----------

SELECT COUNT(*) FROM task_4

-- COMMAND ----------

SELECT * FROM task_4


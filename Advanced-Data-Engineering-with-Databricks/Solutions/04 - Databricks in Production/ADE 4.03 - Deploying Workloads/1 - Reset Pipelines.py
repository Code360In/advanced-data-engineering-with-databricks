# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC 
# MAGIC <div style="text-align: center; line-height: 0; padding-top: 9px;">
# MAGIC   <img src="https://databricks.com/wp-content/uploads/2018/03/db-academy-rgb-1200px.png" alt="Databricks Learning" style="width: 600px">
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC # Reset Pipelines
# MAGIC 
# MAGIC In this notebook, code is provided to remove all existing databases, data, and tables. 
# MAGIC 
# MAGIC Code is then provided to redeclare each table used in the architecture.
# MAGIC 
# MAGIC This notebook should be run prior to scheduling jobs.

# COMMAND ----------

# MAGIC %run ../../Includes/module-4/setup-lesson-4.03.1-reset-and-install-datasets

# COMMAND ----------

# MAGIC %md
# MAGIC We'll be using the **`bronze_dev`** table, which is a clone that already contains all of our daily data.

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES

# COMMAND ----------

# MAGIC %md
# MAGIC Code to declare all the other tables in our pipelines are provided below.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS heart_rate_silver
# MAGIC (device_id LONG, time TIMESTAMP, heartrate DOUBLE, bpm_check STRING)
# MAGIC USING DELTA
# MAGIC LOCATION '${da.paths.user_db}/heart_rate_silver'

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS workouts_silver
# MAGIC (user_id INT, workout_id INT, time TIMESTAMP, action STRING, session_id INT)
# MAGIC USING DELTA
# MAGIC LOCATION '${da.paths.user_db}/workouts_silver'

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS users
# MAGIC (alt_id STRING, dob DATE, sex STRING, gender STRING, first_name STRING, last_name STRING, street_address STRING, city STRING, state STRING, zip INT, updated TIMESTAMP)
# MAGIC USING DELTA
# MAGIC LOCATION '${da.paths.user_db}/users'

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS gym_mac_logs
# MAGIC (first_timestamp DOUBLE, gym BIGINT, last_timestamp DOUBLE, mac STRING)
# MAGIC USING delta
# MAGIC LOCATION '${da.paths.user_db}/gym_mac_logs'

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS completed_workouts
# MAGIC (user_id INT, workout_id INT, session_id INT, start_time TIMESTAMP, end_time TIMESTAMP, in_progress BOOLEAN)
# MAGIC USING DELTA
# MAGIC LOCATION '${da.paths.user_db}/completed_workouts'

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS workout_bpm
# MAGIC (user_id INT, workout_id INT, session_id INT, time TIMESTAMP, heartrate DOUBLE)
# MAGIC USING DELTA
# MAGIC LOCATION '${da.paths.user_db}/workout_bpm'

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS user_bins
# MAGIC (user_id BIGINT, age STRING, gender STRING, city STRING, state STRING)
# MAGIC USING DELTA
# MAGIC LOCATION '${da.paths.user_db}/user_bins'

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS registered_users
# MAGIC (device_id long, mac_address string, registration_timestamp double, user_id long)
# MAGIC USING DELTA 
# MAGIC LOCATION '${da.paths.user_db}/registered_users'

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS user_lookup
# MAGIC (alt_id string, device_id long, mac_address string, user_id long)
# MAGIC USING DELTA 
# MAGIC LOCATION '${da.paths.user_db}/user_lookup'

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS workout_bpm_summary
# MAGIC (workout_id INT, session_id INT, user_id BIGINT, age STRING, gender STRING, city STRING, state STRING, min_bpm DOUBLE, avg_bpm DOUBLE, max_bpm DOUBLE, num_recordings BIGINT)
# MAGIC USING DELTA 
# MAGIC LOCATION '${da.paths.user_db}/workout_bpm_summary'

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE VIEW IF NOT EXISTS gym_user_stats AS (
# MAGIC SELECT gym, mac_address, date, workouts, 
# MAGIC        (last_timestamp - first_timestamp)/60 AS minutes_in_gym, 
# MAGIC        (to_unix_timestamp(end_workout) - to_unix_timestamp(start_workout))/60 AS minutes_exercising
# MAGIC FROM gym_mac_logs c
# MAGIC INNER JOIN (
# MAGIC   SELECT b.mac_address, 
# MAGIC          to_date(start_time) AS date, 
# MAGIC          collect_set(workout_id) AS workouts, 
# MAGIC          min(start_time) AS start_workout, 
# MAGIC          max(end_time) AS end_workout
# MAGIC   FROM completed_workouts a
# MAGIC   INNER JOIN user_lookup b
# MAGIC   ON a.user_id = b.user_id
# MAGIC   GROUP BY mac_address, to_date(start_time)
# MAGIC ) d
# MAGIC ON c.mac = d.mac_address AND 
# MAGIC    to_date(CAST(c.first_timestamp AS timestamp)) = d.date)

# COMMAND ----------

# MAGIC %md
# MAGIC For this demo, we're only focused on processing those data coming through our multiplex bronze table, so we'll bypass the incremental loading for the **`gym_mac_logs`** and **`user_lookup`** tables and recreate the final results with a direct read of all files.

# COMMAND ----------

(spark.read
      .json(f"{DA.data_source_uri}/gym-logs")
      .write
      .mode("overwrite")
      .saveAsTable("gym_mac_logs"))

(spark.read
      .format("json")
      .schema("device_id long, mac_address string, registration_timestamp double, user_id long")
      .load(f"{DA.data_source_uri}/user-reg")
      .selectExpr(f"sha2(concat(user_id,'BEANS'), 256) AS alt_id", "device_id", "mac_address", "user_id")
      .write
      .mode("overwrite")
      .saveAsTable("user_lookup"))

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES

# COMMAND ----------

# MAGIC %md
# MAGIC Unlike other lessons, we will **NOT** be be executing our **`DA.cleanup()`** command<br/>
# MAGIC as we want these assets to persist through all the notebooks in this demo.

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC &copy; 2022 Databricks, Inc. All rights reserved.<br/>
# MAGIC Apache, Apache Spark, Spark and the Spark logo are trademarks of the <a href="https://www.apache.org/">Apache Software Foundation</a>.<br/>
# MAGIC <br/>
# MAGIC <a href="https://databricks.com/privacy-policy">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use">Terms of Use</a> | <a href="https://help.databricks.com/">Support</a>

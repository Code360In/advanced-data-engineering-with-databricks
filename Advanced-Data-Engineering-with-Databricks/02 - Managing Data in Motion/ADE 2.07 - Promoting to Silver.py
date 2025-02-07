# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC 
# MAGIC <div style="text-align: center; line-height: 0; padding-top: 9px;">
# MAGIC   <img src="https://databricks.com/wp-content/uploads/2018/03/db-academy-rgb-1200px.png" alt="Databricks Learning" style="width: 600px">
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC ## Promoting to Silver
# MAGIC 
# MAGIC Here we'll pull together the concepts of streaming from Delta Tables, deduplication, and quality enforcement to finalize our approach to our silver table.
# MAGIC 
# MAGIC <img src="https://files.training.databricks.com/images/ade/ADE_arch_heartrate_silver.png" width="60%" />
# MAGIC 
# MAGIC ## Learning Objectives
# MAGIC By the end of this lesson, students will be able to:
# MAGIC - Apply table constraints to Delta Lake tables
# MAGIC - Use flagging to identify records failing to meet certain conditions
# MAGIC - Apply de-duplication within an incremental microbatch
# MAGIC - Use **`MERGE`** to avoid inserting duplicate records to a Delta Lake table

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

# MAGIC %run ../Includes/module-2/setup-lesson-2.07-silver-setup

# COMMAND ----------

# MAGIC %md
# MAGIC Begin by resetting your table and checkpoint to make sure there are no conflicts from previous writes.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS heart_rate_silver
# MAGIC (device_id LONG, time TIMESTAMP, heartrate DOUBLE, bpm_check STRING)
# MAGIC USING DELTA

# COMMAND ----------

# MAGIC %md
# MAGIC ## Table Constraint
# MAGIC Add a table constraint before inserting data. Name this constraint **`dateWithinRange`** and make sure that the time is greater than January 1, 2017.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- TODO
# MAGIC ALTER TABLE -- <FILL-IN>

# COMMAND ----------

# MAGIC %md
# MAGIC Note that adding and removing constraints is recorded in the transaction log.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY heart_rate_silver

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define a Streaming Read and Transformation
# MAGIC Use the cell below to create a streaming read that includes:
# MAGIC 1. A filter for the topic **`bpm`**
# MAGIC 2. Logic to flatten the JSON payload and cast data to the appropriate schema
# MAGIC 3. A **`bpm_check`** column to flag negative records
# MAGIC 4. A duplicate check on **`device_id`** and **`time`** with a 30 second watermark on **`time`**

# COMMAND ----------

# TODO
streamingDF = (
# <FILL_IN>
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Upsert Query
# MAGIC Below, the upsert class used in the previous notebooks is provided.

# COMMAND ----------

class Upsert:
    def __init__(self, sql_query, update_temp="stream_updates"):
        self.sql_query = sql_query
        self.update_temp = update_temp 
        
    def upsertToDelta(self, microBatchDF, batch):
        microBatchDF.createOrReplaceTempView(self.update_temp)
        microBatchDF._jdf.sparkSession().sql(self.sql_query)

# COMMAND ----------

# MAGIC %md
# MAGIC Use the cell below to define the upsert query to instantiate our class. 
# MAGIC 
# MAGIC Alternatetively, <a href="https://docs.databricks.com/delta/delta-update.html#upsert-into-a-table-using-merge&language-python" target="_blank">consult the documentation</a> and try implementing this using the **`DeltaTable`** Python class.

# COMMAND ----------

# TODO
sql_query = """<FILL-IN>"""
 
streamingMerge=Upsert(sql_query)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Apply Upsert and Write
# MAGIC Now execute a write with trigger once logic to process all existing data from the bronze table.

# COMMAND ----------

def process_silver_heartrate():
    query = (streamingDF
        .writeStream
        .foreachBatch(streamingMerge.upsertToDelta)
        .outputMode("update")
        .option("checkpointLocation", f"{DA.paths.checkpoints}/recordings.chk")
        .trigger(once=True)
        .start())
    
    query.awaitTermination()
    
process_silver_heartrate()

# COMMAND ----------

# MAGIC %md
# MAGIC We should see the same number of total records in our silver table as the deduplicated count from the lesson 2.5, and a small percentage of these will correctly be flagged with "Negative BPM".

# COMMAND ----------

new_total = spark.read.table("heart_rate_silver").count()

print(f"Lesson #5: {731987:,}")
print(f"New Total: {new_total:,}")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*)
# MAGIC FROM heart_rate_silver
# MAGIC WHERE bpm_check = "Negative BPM"

# COMMAND ----------

# MAGIC %md
# MAGIC Now land a new batch of data and propagate changes through bronze into the silver table.
# MAGIC 
# MAGIC <img src="https://files.training.databricks.com/images/icon_note_32.png"> The following two methods were recreated for us from previous lessons

# COMMAND ----------

DA.data_factory.load() # Load a day's worth of data
DA.process_bronze()    # Execute 1 iteration of the daily to bronze stream

# COMMAND ----------

process_silver_heartrate()

# COMMAND ----------

end_total = spark.read.table("heart_rate_silver").count()

print(f"Lesson #5: {731987:,}")
print(f"New Total: {new_total:,}")
print(f"End Total:   {end_total:,}")

# COMMAND ----------

# MAGIC %md 
# MAGIC Run the following cell to delete the tables and files associated with this lesson.

# COMMAND ----------

DA.cleanup()

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC &copy; 2022 Databricks, Inc. All rights reserved.<br/>
# MAGIC Apache, Apache Spark, Spark and the Spark logo are trademarks of the <a href="https://www.apache.org/">Apache Software Foundation</a>.<br/>
# MAGIC <br/>
# MAGIC <a href="https://databricks.com/privacy-policy">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use">Terms of Use</a> | <a href="https://help.databricks.com/">Support</a>

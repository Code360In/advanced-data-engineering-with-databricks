# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC 
# MAGIC <div style="text-align: center; line-height: 0; padding-top: 9px;">
# MAGIC   <img src="https://databricks.com/wp-content/uploads/2018/03/db-academy-rgb-1200px.png" alt="Databricks Learning" style="width: 600px">
# MAGIC </div>

# COMMAND ----------

# MAGIC %md
# MAGIC # Deidentified PII Access
# MAGIC 
# MAGIC This lesson explores approaches for reducing risk of PII leakage while working with potentially sensitive information for analytics and reporting.
# MAGIC 
# MAGIC <img src="https://files.training.databricks.com/images/ade/ADE_arch_user_bins.png" width="60%" />
# MAGIC 
# MAGIC ## Learning Objectives
# MAGIC By the end of this lesson, students will be able to:
# MAGIC - Apply dynamic views to sensitive data to obscure columns containing PII
# MAGIC - Use dynamic views to filter data, only showing relevant rows to relevant audiences
# MAGIC - Create binned tables to generalize data and obscure PII

# COMMAND ----------

# MAGIC %md
# MAGIC Begin by running the following cell to set up relevant databases and paths.

# COMMAND ----------

# MAGIC %run ../Includes/module-3/setup-lesson-3.05-ade_setup

# COMMAND ----------

# MAGIC %md
# MAGIC ## Dynamic Views
# MAGIC 
# MAGIC Databricks <a href="https://docs.databricks.com/security/access-control/table-acls/object-privileges.html#dynamic-view-functions" target="_blank">dynamic views</a> allow user or group identity ACLs to be applied to data at the column (or row) level.
# MAGIC 
# MAGIC Database administrators can configure data access privileges to disallow access to a source table and only allow users to query a redacted view. Users with sufficient privileges will be able to see all fields, while restricted users will be shown arbitrary results, as defined at view creation.

# COMMAND ----------

# MAGIC %md
# MAGIC Consider our **`users`** table with the following columns.

# COMMAND ----------

spark.table("users").columns

# COMMAND ----------

# MAGIC %md
# MAGIC Obviously first name, last name, date of birth, and street address are problematic. We'll also obfuscate zip code (as zip code combined with date of birth has a very high confidence in identifying data).

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW users_vw AS
# MAGIC SELECT
# MAGIC   alt_id,
# MAGIC   CASE 
# MAGIC     WHEN is_member('ade_demo') THEN dob
# MAGIC     ELSE 'REDACTED'
# MAGIC   END AS dob,
# MAGIC   sex,
# MAGIC   gender,
# MAGIC   CASE 
# MAGIC     WHEN is_member('ade_demo') THEN first_name
# MAGIC     ELSE 'REDACTED'
# MAGIC   END AS first_name,
# MAGIC   CASE 
# MAGIC     WHEN is_member('ade_demo') THEN last_name
# MAGIC     ELSE 'REDACTED'
# MAGIC   END AS last_name,
# MAGIC   CASE 
# MAGIC     WHEN is_member('ade_demo') THEN street_address
# MAGIC     ELSE 'REDACTED'
# MAGIC   END AS street_address,
# MAGIC   city,
# MAGIC   state,
# MAGIC   CASE 
# MAGIC     WHEN is_member('ade_demo') THEN zip
# MAGIC     ELSE 'REDACTED'
# MAGIC   END AS zip,
# MAGIC   updated
# MAGIC FROM users

# COMMAND ----------

# MAGIC %md
# MAGIC Now when we query from **`users_vw`**, only members of the group **`ade_demo`** will be able to see results in plain text.
# MAGIC 
# MAGIC **NOTE**: You may not have privileges to create groups or assign membership. Your instructor should be able to demonstrate how group membership will change query results.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM users_vw

# COMMAND ----------

# MAGIC %md
# MAGIC ## Adding Conditional Row Access
# MAGIC 
# MAGIC Adding views with **`WHERE`** clauses to filter source data on different conditions for teams throughout an organization can be a beneficial option for granting access to only the necessary data to each audience. Dynamic views add the option to create these views with full access to underlying data for users with elevated privileges.
# MAGIC 
# MAGIC Note the views can be layered on top of one another; below, the **`users_vw`** from the previous step is modified with conditional access. Users that aren't members of the specified group will only be able to see records from the city of Los Angeles that have been updated after the specified date.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW users_la_vw AS
# MAGIC SELECT * FROM users_vw
# MAGIC WHERE 
# MAGIC   CASE 
# MAGIC     WHEN is_member('ade_demo') THEN TRUE
# MAGIC     ELSE city = "Los Angeles" AND updated > "2019-12-12"
# MAGIC   END

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM users_la_vw

# COMMAND ----------

# MAGIC %md
# MAGIC ## Provide Provisional Access to **`user_lookup`** Table
# MAGIC 
# MAGIC Our **`user_lookup`** table allows our ETL pipelines to match up our various identifiers with our **`alt_id`** and pull demographic information, as necessary.
# MAGIC 
# MAGIC Most of our team will not need access to our full PII, but may need to use this table to match up various natural keys from different systems.
# MAGIC 
# MAGIC Define a dynamic view named **`user_lookup_vw`** below that provides conditional access to the **`alt_id`** but full access to the other info in our **`user_lookup`** table.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- TODO
# MAGIC CREATE OR REPLACE VIEW user_lookup_vw AS
# MAGIC -- FILL_IN
# MAGIC FROM user_lookup

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM user_lookup_vw

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generalize PII in Aggregate Tables
# MAGIC 
# MAGIC Another approach to reducing chance of exposing PII is only providing access to data at a less specific level.
# MAGIC 
# MAGIC In this section, we'll assign users to age bins while maintaining their gender, city, and state information. This will provide sufficient demographic information to build comparative dashboards without revealing specific user identity.

# COMMAND ----------

usersDF = spark.table("users")

# COMMAND ----------

# MAGIC %md
# MAGIC Here we're just defining custom logic for replacing values with manually-specified labels.

# COMMAND ----------

def age_bins(dob_col):
    age_col = F.floor(F.months_between(F.current_date(), dob_col)/12).alias("age")
    return (F.when((age_col < 18), "under 18")
            .when((age_col >= 18) & (age_col < 25), "18-25")
            .when((age_col >= 25) & (age_col < 35), "25-35")
            .when((age_col >= 35) & (age_col < 45), "35-45")
            .when((age_col >= 45) & (age_col < 55), "45-55")
            .when((age_col >= 55) & (age_col < 65), "55-65")
            .when((age_col >= 65) & (age_col < 75), "65-75")
            .when((age_col >= 75) & (age_col < 85), "75-85")
            .when((age_col >= 85) & (age_col < 95), "85-95")
            .when((age_col >= 95), "95+")
            .otherwise("invalid age").alias("age"))

# COMMAND ----------

# MAGIC %md
# MAGIC Because this aggregate view of demographic information is no longer personally identifiable, we can safely store this using our natural key.
# MAGIC 
# MAGIC We'll reference our **`user_lookup`** table to match our IDs.

# COMMAND ----------

lookupDF = spark.table("user_lookup").select("alt_id", "user_id")
binsDF = usersDF.join(lookupDF, ["alt_id"], "left").select("user_id", age_bins(F.col("dob")),"gender", "city", "state")

# COMMAND ----------

display(binsDF)

# COMMAND ----------

# MAGIC %md
# MAGIC This binned demographic data will be saved to a table for our analysts to reference.

# COMMAND ----------

spark.sql("DROP TABLE IF EXISTS user_bins")
dbutils.fs.rm(Paths.userBins, True)

(binsDF.write
  .format("delta")
  .option("path", Paths.userBins)
  .mode("overwrite")
  .saveAsTable("user_bins"))

# COMMAND ----------

# MAGIC %md
# MAGIC Note that as currently implemented, each time this logic is processed, all records will be overwritten with newly calculated values. To decrease chances of identifying birth date at binned boundaries, random noise could be added to the values used to calculate age bins (generally keeping age bins accurate, but reducing the likelihood of transitioning a user to a new bin on their exact birthday).

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

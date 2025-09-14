# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import sys

# import Constant
from pyspark.sql import Row, SparkSession


def create_dataframe_from_params(spark, params):
    # Create a Row object with the parameters
    row = Row(**params)

    # Create a DataFrame from the Row object
    df = spark.createDataFrame([row])

    return df


if __name__ == "__main__":

    spark = SparkSession.builder.appName("SampleSparkJob").getOrCreate()
    spark_context = spark.sparkContext
    spark_context.setLogLevel("DEBUG")

    print("spark.synapse.pool.name : " + spark.conf.get("spark.synapse.pool.name"))
    print()
    print(f"sys.argv : " + str(sys.argv))
    print("spark.driver.cores : " + spark.conf.get("spark.driver.cores"))
    print("spark.driver.memory : " + spark.conf.get("spark.driver.memory"))
    print("spark.executor.cores : " + spark.conf.get("spark.executor.cores"))
    print("spark.executor.memory : " + spark.conf.get("spark.executor.memory"))
    print("spark.executor.instances: " + spark.conf.get("spark.executor.instances"))
    print()
    print(
        "spark.dynamicAllocation.enabled : "
        + spark.conf.get("spark.dynamicAllocation.enabled")
    )
    print(
        "spark.dynamicAllocation.maxExecutors : "
        + spark.conf.get("spark.dynamicAllocation.maxExecutors")
    )
    print(
        "spark.dynamicAllocation.minExecutors : "
        + spark.conf.get("spark.dynamicAllocation.minExecutors")
    )

    params = {"param1": "value1", "param2": "value2"}
    df = create_dataframe_from_params(spark, params)
    df.show()

    deltaTablePath = "Tables/ParamsTable"
    df.write.option("overwriteSchema", "true").mode("overwrite").format("delta").save(
        deltaTablePath
    )

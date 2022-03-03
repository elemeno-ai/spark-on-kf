import kfp
import kfp.dsl as dsl
from kfp.dsl import PipelineConf
import time
import yaml

KFP_ENDPOINT = "http://localhost:8005"
SPARK_COMPLETED_STATE = "COMPLETED"
SPARK_APPLICATION_KIND = "sparkapplications"
EXECUTORS = 3
TOTAL_TIMEOUT = 600


# Load and modify spark app behavior
def get_spark_app_manifest():
    with open("k8s/spark-application.yaml", "r") as stream:
        spark_app = yaml.safe_load(stream)
    epoch1 = int(time.time())
    spark_app["metadata"]["name"] = spark_app["metadata"]["name"].format(epoch=epoch1)
    spark_app["spec"]["executor"]["instances"] = EXECUTORS
    return spark_app


@dsl.pipeline(
    name="Spark App pipeline",
    description=""
)
def spark_job_pipeline():
    dsl.ResourceOp(
        name="spark-app",
        k8s_resource=get_spark_app_manifest(),
        success_condition="status.applicationState.state == {target_status}"
            .format(target_status=SPARK_COMPLETED_STATE),
        action="apply",
        attribute_outputs={"executors": "{.status.executorState}"}
    )


if __name__ == "__main__":
    # Compile the pipeline
    epoch = int(time.time())
    import kfp.compiler as compiler
    import logging

    logging.basicConfig(level=logging.INFO)
    pipeline_func = spark_job_pipeline
    pipeline_filename = pipeline_func.__name__ + f"{epoch}" + ".yaml"
    pipe_cfg = PipelineConf().set_timeout(TOTAL_TIMEOUT)
    compiler.Compiler().compile(pipeline_func, pipeline_filename, pipeline_conf=pipe_cfg)
    logging.info(f"Generated pipeline file: {pipeline_filename}.")

    # Run pipeline
    client = kfp.Client(KFP_ENDPOINT)
    client.create_run_from_pipeline_package(pipeline_filename, arguments={})

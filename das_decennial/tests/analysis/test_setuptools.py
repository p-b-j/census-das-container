import pytest
import analysis.tools.setuptools


@pytest.mark.parametrize(
    "save_location,spark_loglevel,logname,num_core_nodes,analysis_script,error_message", [
        (None, "ERROR", "testlog", 1, "test_script",
         "Need to specify local directory where the results of analysis will be saved"),
        ("test_location", "flarf", "testlog", 1, "test_script", "Invalid Spark loglevel"),
        ("test_location", "ERROR", "testlog", -1, "test_script", "num_core_nodes must be positive integer"),
        ("test_location", "ERROR", "testlog", "flarf", "test_script", "num_core_nodes must be positive integer"),
        ("test_location", "ERROR", None, 1, "test_script",
         "If not using command line, must pass logname, num_core_nodes, and analysis_script"),
        ("test_location", "ERROR", "testlog", None, "test_script",
         "If not using command line, must pass logname, num_core_nodes, and analysis_script"),
        ("test_location", "ERROR", "testlog", 1, None,
         "If not using command line, must pass logname, num_core_nodes, and analysis_script"),
        ("test_location", "ERROR", None, None, None,
         "If not using command line, must pass logname, num_core_nodes, and analysis_script"),
    ]
)
def test_setup_errors(save_location, spark_loglevel, logname, num_core_nodes, analysis_script, error_message):
    """
    Test the setup function in analysis.tools.setuptools, which creates an analysis object
    :param save_location: local directory where results of analysis will be saved
    :param spark_loglevel: the loglevel to set spark session
    :param output: set of expected outputs
    :return:
    """
    with pytest.raises(Exception) as excinfo:
        analysis.tools.setuptools.setup(save_location=save_location, spark_loglevel=spark_loglevel, cli_args=False,
                                        logname=logname, num_core_nodes=num_core_nodes, analysis_script=analysis_script)
        assert str(excinfo.value) == error_message


@pytest.mark.parametrize(
    "save_location,spark_loglevel,logname,num_core_nodes,analysis_script,output", [
        ("test_location", "ERROR", "testlog", 1, "test_script",
         {"save_location": "test_location/testlog/",
          "save_location_s3": "s3://uscb-decennial-ite-das/users/test_location/testlog/",
          "save_location_linux": "/mnt/users/test_location/testlog/"}
         ),
        ("test_location", "ERROR", "testlog", 8, "test_script",
         {"save_location": "test_location/testlog/",
          "save_location_s3": "s3://uscb-decennial-ite-das/users/test_location/testlog/",
          "save_location_linux": "/mnt/users/test_location/testlog/"}
         )
    ]
)
def test_setup(save_location, spark_loglevel, logname, num_core_nodes, analysis_script, output):
    """
    Test the setup function in analysis.tools.setuptools, which creates an analysis object
    :param save_location: local directory where results of analysis will be saved
    :param spark_loglevel: the loglevel to set spark session
    :param output: set of expected outputs
    :return:
    """
    analysis_object = analysis.tools.setuptools.setup(save_location=save_location, spark_loglevel=spark_loglevel,
                                                      cli_args=False, logname=logname, num_core_nodes=num_core_nodes,
                                                      analysis_script=analysis_script)

    assert analysis_object.save_location == output["save_location"]
    assert analysis_object.save_location_s3 == output["save_location_s3"]
    assert analysis_object.save_location_linux == output["save_location_linux"]

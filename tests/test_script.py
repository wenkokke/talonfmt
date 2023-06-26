def test_talonfmt_version() -> None:
    import subprocess

    import talonfmt

    actual_output = (
        subprocess.check_output(["talonfmt", "--version"]).decode("utf-8").strip()
    )
    assert actual_output == f"talonfmt, version {talonfmt.__version__}"

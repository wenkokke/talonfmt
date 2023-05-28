def test_talonfmt_version() -> None:
    import talonfmt
    import subprocess

    actual_output = (
        subprocess.check_output(["talonfmt", "--version"]).decode("utf-8").strip()
    )
    assert actual_output == f"talonfmt, version {talonfmt.__version__}"

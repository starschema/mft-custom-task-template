from mft import MFT


def run(mft: MFT) -> None:
    """Write your custom task logic here."""
    # Read input parameters
    example = mft.input.get_string("exampleInput")

    # Your task logic goes here
    result = f"Processed: {example}"

    # Write output parameters
    mft.output.set_string("exampleOutput", result)


# --- Boilerplate (do not modify) ---
if __name__ == "__main__":
    try:
        task = MFT.init()
    except Exception as e:
        MFT.Err(str(e), error_id="InitError")
    try:
        run(task)
        MFT.Ok()
    except Exception as e:
        MFT.Err(str(e))

"""Safe English CSV diagnostics keyed by the parser's stable reasons."""

ROW_MESSAGES = {
    "column_count": "Match the number of columns in the header.",
    "asset_empty": "Enter a device name.",
    "asset_too_long": "Use a device name of at most 60 characters.",
    "source_too_long": "Shorten the source name.",
    "time_format": "Use a supported timestamp format.",
    "time_impossible": "Enter a valid date and time.",
    "time_nonexistent": "Use a time that exists in the site timezone.",
    "time_ambiguous": "Include the UTC offset to identify the time.",
    "interval_reversed": "The interval end must be after its start.",
    "value_empty": "Enter a measured value.",
    "value_ambiguous": "Use an unambiguous decimal format.",
    "value_ambiguous_comma": "Put decimal commas in quoted fields when using a comma delimiter.",
    "value_not_number": "Enter a number.",
    "value_too_precise": "Use up to three decimal places.",
    "value_too_large": "Use a smaller value.",
    "negative": "Enter zero or a positive value.",
    "conflict": "Different values exist for the same source and interval. Correct the readings.",
    "interval_overlap": "This reading overlaps another interval from the same source. Correct the times.",
}

STRUCTURAL_MESSAGES = {
    "empty_input": "Choose a CSV file or paste its contents.",
    "too_large": "Use a file of at most 10 MiB.",
    "not_utf8": "Save the file as UTF-8.",
    "delimiter_ambiguous": "Use commas or semicolons consistently.",
    "single_column": "Separate the columns with commas or semicolons.",
    "quote_unclosed": "Close the quoted field.",
    "quote_malformed": "Fix the quoted field.",
    "duplicate_role": "Keep one column for each field.",
    "competing_time_columns": "Use timestamps or interval bounds consistently.",
    "missing_asset": "Add a device column.",
    "missing_time": "Add a timestamp or interval bounds.",
    "missing_value": "Add a measured-value column.",
    "counter_needs_timestamp": "Counter readings require a timestamp.",
    "too_many_rows": "Use up to 150,000 data rows.",
    "no_data_rows": "Add data rows below the header.",
}

QUESTION_MESSAGES = {
    "value_kind": "Choose the column that contains the measured value.",
    "power_meaning": "Confirm whether the power value is the interval average.",
    "timezone": "Confirm how to read timestamps without a UTC offset.",
    "interval_duration": "Enter the interval length for this source.",
    "scope": "Confirm whether the devices measure separate loads.",
    "asset_choice": "Choose which existing device to use, or add a new device.",
    "other_source": "This device already has a source. Review the mapping.",
    "stream_assets": "Use one device for this source.",
    "asset_streams": "Choose separate devices or resolve the sources before importing.",
}

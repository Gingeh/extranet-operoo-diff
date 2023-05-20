from typing import Callable, Optional
import xml.etree.ElementTree as Xet
import sys
import polars as pl

pl.Config().set_tbl_rows(-1).set_tbl_hide_column_data_types()


def read_xml(file: str) -> pl.LazyFrame:
    # The Operoo report has two spaces at the start of
    # the file which prevent it from being parsed correctly
    with open(file, mode="r", encoding="utf8") as f:
        original = f.read()
    root = Xet.fromstring(original[2:])
    namespace = {"doc": "urn:schemas-microsoft-com:office:spreadsheet"}

    needed_columns = [
        "Profile Id",
        "Person Name",
        "Profile Owner's Name ",
        "Profile Owner's Email",
        "Profile Owner's Mobile Phone",
        "Person Birth Date",
    ]
    columns = [
        cell.text for cell in root.findall(".//doc:Row[1]/doc:Cell/doc:Data", namespace)
    ]
    data = {}
    for column in needed_columns:
        data[column] = []

    for row in root.findall(".//doc:Row", namespace)[1:]:
        for i, column in enumerate(columns):
            if column in needed_columns:
                data[column].append(
                    row.find(f"doc:Cell[{i+1}]/doc:Data", namespace).text
                )
    return pl.DataFrame(data).lazy()


if len(sys.argv) != 3:
    print(f"USAGE: {sys.argv[0]} <Extranet CSV file> <Operoo XLS file>")
    sys.exit(1)

extranet = pl.scan_csv(sys.argv[1], ignore_errors=True)
operoo = read_xml(sys.argv[2])

# Casting data types
operoo = operoo.with_column(pl.col("Profile Id").cast(pl.Int64()))

joined = extranet.join(operoo, left_on="RegID", right_on="Profile Id", how="inner")


def diff_map(
    extranet_column: str,
    operoo_column: str,
    function: Optional[Callable[[pl.Expr], pl.Expr]] = None,
    extranet_function: Callable[[pl.Expr], pl.Expr] = lambda x: x,
    operoo_function: Callable[[pl.Expr], pl.Expr] = lambda x: x,
    filter: pl.Expr = pl.lit(True),
):
    if function is not None:
        extranet_function = function
        operoo_function = function

    print(
        joined.filter(
            extranet_function(pl.col(extranet_column))
            != operoo_function(pl.col(operoo_column))
        )
        .filter(filter)
        .select(
            [
                pl.col("RegID"),
                extranet_function(pl.col(extranet_column)).prefix("Extranet: "),
                operoo_function(pl.col(operoo_column)).prefix("Operoo: "),
            ]
        )
        .collect()
    )


# Member IDs in Extranet but not Operoo
missing_from_operoo = (
    extranet.join(operoo, left_on="RegID", right_on="Profile Id", how="anti")
    .with_column(
        pl.col("RegID").map(lambda x: None).cast(pl.Int64()).alias("Profile Id")
    )
    .select(
        [
            pl.col("RegID").prefix("Extranet: "),
            pl.col("Profile Id").prefix("Operoo: "),
            pl.col("FullName").alias("Name"),
        ]
    )
    .collect()
)

# Member IDs in Operoo but not Extranet
missing_from_extranet = (
    operoo.join(extranet, left_on="Profile Id", right_on="RegID", how="anti")
    .with_column(
        pl.col("Profile Id").map(lambda x: None).cast(pl.Int64()).alias("RegID")
    )
    .select(
        [
            pl.col("RegID").prefix("Extranet: "),
            pl.col("Profile Id").prefix("Operoo: "),
            pl.col("Person Name").alias("Name"),
        ]
    )
    .collect()
)

# Shown in one table
print(pl.concat([missing_from_extranet, missing_from_operoo]))

# Member's full name
# Note: Extranet uses preferred name, Operoo uses given name
diff_map(
    "FullName",
    "Person Name",
    function=lambda x: x.str.to_lowercase().str.strip().str.replace_all(r"\s+", " "),
)

# Primary contact name
diff_map(
    "Primary Contact Firstname",
    "Profile Owner's Name ",
    extranet_function=lambda x: pl.concat_str(
        [x, pl.col("Primary Contact Surname")], sep=" "
    )
    .str.to_lowercase()
    .str.strip()
    .str.replace_all(r"\s+", " "),
    operoo_function=lambda x: x.str.to_lowercase()
    .str.strip()
    .str.replace_all(r"\s+", " "),
    # Only check youth members
    filter=pl.col("ClassID").is_in(["JOEY", "CUB", "SCOUT", "VENT"]),  # ROVER?
)
# Primary contact email
diff_map(
    "Primary Contact Email",
    "Profile Owner's Email",
    function=lambda x: x.str.to_lowercase().str.strip(),
    # Only check youth members
    filter=pl.col("ClassID").is_in(["JOEY", "CUB", "SCOUT", "VENT"]),  # ROVER?
)

# Primary contact mobile number
diff_map(
    "Primary Contact Mobile",
    "Profile Owner's Mobile Phone",
    # Strip area codes and leading zeros
    function=lambda x: x.cast(pl.Utf8()).str.replace(r"\+61", "").cast(pl.Int64()),
    # Only check youth members
    filter=pl.col("ClassID").is_in(["JOEY", "CUB", "SCOUT", "VENT"]),  # ROVER?
)

# Member's date of birth
diff_map(
    "DOB",
    "Person Birth Date",
    # Extranet uses "yyyy-mm-dd", Operoo uses "d Month yyyy"
    extranet_function=lambda x: x.str.strptime(pl.Date, "%F"),
    operoo_function=lambda x: x.str.strptime(pl.Date, "%e %B %Y"),
)

# Member's city/state
# Note: good luck
# diff_map("HomeSuburb", "Person City", function = lambda x: x.str.to_lowercase().str.strip())

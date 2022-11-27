# extranet-operoo-diff

A Python script to identify possible errors and inconsistencies in Extranet and Operoo.

**NOTE: There will likely be false-positives can be safely ignored**

## Installation

1. Make sure you have Python and git installed
1. Clone this repository:

    ```bash
    git clone https://github.com/Gingeh/extranet-operoo-diff.git
    cd extranet-operoo-diff
    ```

1. Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

```bash
extranet-operoo-diff.py <Extranet CSV file> <Operoo XLS file>
```

(See below for instructions for exporting the required files)

### Example output

```text
                      . . .
shape: (2, 3)
┌───────┬───────────────┬───────────────────────────┐
│ RegID ┆ Extranet: DOB ┆ Operoo: Person Birth Date │
╞═══════╪═══════════════╪═══════════════════════════╡
│ 12345 ┆ 1970-01-01    ┆ null                      │
├╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│ 67890 ┆ 2005-03-08    ┆ 2005-03-06                │
└───────┴───────────────┴───────────────────────────┘
                      . . .
```

### What will be checked

- Members in one system but not the other
- Member names, **a lot of false positives** because of preferred names
- Primary contact/profile owner names (youth only)
- Primary contact/profile owner emails (youth only)
- Primary contact/profile owner mobile numbers (youth only)
- Member birth dates

(Most comparisons are case-insensitive)

## Data Collection

### Extranet

1) Using a PC/Mac, go to [https://extranet.act.scouts.asn.au/](https://extranet.act.scouts.asn.au/)
2) Log in to Extranet.
3) Select "Membership" from the menu in the top right of the page.
4) Hover over "Statistical Reports" and then click on "Group Report" in the sub-menu.
5) Click on the "Group Report" button.
6) Click on the number in the "Grand Total" column for your group.
7) Scroll down to the bottom of the newly opened page.
8) Click on "Export to CSV Format"
9) Your browser will save a file with a name in the format `YYYY-MM-DD.csv` (eg `2022-11-27.csv`)

### Operoo

1) Using a PC/Mac, go to [https://groups.operoo.com/users/sign_in](https://groups.operoo.com/users/sign_in)
2) Log in to Operoo.
3) If not already there, select your Group from the menu in the top left corner of the page.
4) Select "Reports/Archives" from the menu bar down the left hand side of the page.
5) Select "Export Profiles" from the list of options.
6) Click on the "Generate" button next to the "Export all profile fields" option.
7) Wait for the process to complete and then click on the newly generated profile report at the top of the page.
8) Your browser will save a file with name in the format `report_attachment-<letters_and_numbers>.xls`

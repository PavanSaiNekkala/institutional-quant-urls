# =========================================================
# FINAL DATA SAFETY
# =========================================================

if final_df is None:

    final_df = pd.DataFrame()

if not isinstance(final_df, pd.DataFrame):

    final_df = pd.DataFrame()

# =========================================================
# ENSURE REQUIRED COLUMNS
# =========================================================

required_columns = [

    "Stock",
    "Trade Signal",
    "Institutional Score",
    "Confidence",
    "Current Price"

]

for column in required_columns:

    if column not in final_df.columns:

        if column == "Trade Signal":

            final_df[column] = "WATCH"

        else:

            final_df[column] = 0

# =========================================================
# HANDLE EMPTY DATAFRAME
# =========================================================

if final_df.empty:

    print("=" * 60)
    print("NO VALID STOCK DATA GENERATED")
    print("=" * 60)

    final_df = pd.DataFrame({

        "Stock": [],
        "Trade Signal": [],
        "Institutional Score": [],
        "Confidence": [],
        "Current Price": []

    })

# =========================================================
# REMOVE DUPLICATES
# =========================================================

if "Stock" in final_df.columns:

    final_df = (

        final_df

        .drop_duplicates(
            subset=["Stock"]
        )

        .reset_index(drop=True)

    )

# =========================================================
# FILL MISSING VALUES
# =========================================================

final_df = final_df.fillna(0)

# =========================================================
# SAFE SORTING
# =========================================================

preferred_columns = [

    "Composite Score",
    "Institutional Score",
    "Confidence",
    "Buy Probability"

]

sort_column = None

for column in preferred_columns:

    if column in final_df.columns:

        sort_column = column
        break

try:

    if (

        sort_column is not None
        and not final_df.empty

    ):

        final_df = final_df.sort_values(

            by=sort_column,

            ascending=False

        )

except Exception as e:

    print(
        f"SORT FAILED : {e}"
    )

# =========================================================
# RESET INDEX
# =========================================================

final_df = final_df.reset_index(drop=True)

# =========================================================
# TOP PICKS
# =========================================================

try:

    if not final_df.empty:

        top_picks_df = final_df.head(100)

    else:

        top_picks_df = pd.DataFrame(
            columns=final_df.columns
        )

except Exception as e:

    print(
        f"TOP PICKS FAILED : {e}"
    )

    top_picks_df = pd.DataFrame()

# =========================================================
# PORTFOLIO SAFETY
# =========================================================

if portfolio_df is None:

    portfolio_df = pd.DataFrame()

if not isinstance(portfolio_df, pd.DataFrame):

    portfolio_df = pd.DataFrame()

portfolio_df = portfolio_df.fillna(0)

# =========================================================
# EXPORT CSV FILES
# =========================================================

csv_exports = {

    "enriched_stock_data.csv":
    final_df,

    "institutional_portfolio.csv":
    portfolio_df,

    "top_institutional_picks.csv":
    top_picks_df

}

print("=" * 60)
print("EXPORTING CSV FILES")
print("=" * 60)

for filename, dataframe in csv_exports.items():

    try:

        if dataframe is None:

            dataframe = pd.DataFrame()

        if not isinstance(
            dataframe,
            pd.DataFrame
        ):

            dataframe = pd.DataFrame()

        export_path = (
            OUTPUT_DIR / filename
        )

        dataframe.to_csv(

            export_path,

            index=False

        )

        print(
            f"EXPORTED : {filename}"
        )

    except Exception as e:

        print(
            f"EXPORT FAILED : "
            f"{filename} | {e}"
        )

# =========================================================
# SAFE DUCKDB SAVE
# =========================================================

try:

    if (

        not final_df.empty

        and len(final_df.columns) > 0

    ):

        conn.execute(
            "DROP TABLE IF EXISTS enriched_stocks"
        )

        conn.register(
            "final_df",
            final_df
        )

        conn.execute(
            """
            CREATE TABLE enriched_stocks AS
            SELECT * FROM final_df
            """
        )

        print("DUCKDB SAVED")

    else:

        print(
            "DUCKDB SKIPPED : EMPTY DATAFRAME"
        )

except Exception as e:

    print(
        f"DUCKDB SAVE FAILED : {e}"
    )

# =========================================================
# FINAL SUMMARY
# =========================================================

print("=" * 60)

print(
    f"FINAL STOCK COUNT : "
    f"{len(final_df)}"
)

print(
    f"TOP PICKS COUNT : "
    f"{len(top_picks_df)}"
)

print(
    f"PORTFOLIO COUNT : "
    f"{len(portfolio_df)}"
)

print("=" * 60)

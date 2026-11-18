import json
from pathlib import Path

import pandas as pd
import pandera.pandas as pa

from schema import TRANSACTION_SCHEMA


BASE_DIR = Path(__file__).resolve().parents[2]

RAW_FILE = BASE_DIR / "data/raw/transactions.csv"
VALID_FILE = BASE_DIR / "data/validated/transactions.csv"
INVALID_FILE = BASE_DIR / "data/quarantine/transactions.csv"
REPORT_FILE = BASE_DIR / "reports/validation_report.json"


ALLOWED_CURRENCIES = {"INR"}
ALLOWED_STATUSES = {"SUCCESS", "FAILED"}


def validate_dataset():

    df = pd.read_csv(RAW_FILE)

    # 1. Structural validation
    try:
        df = TRANSACTION_SCHEMA.validate(df)

    except pa.errors.SchemaError as exc:
        raise RuntimeError(
            f"Dataset schema validation failed: {exc}"
        ) from exc

    except pa.errors.SchemaErrors as exc:
        raise RuntimeError(
            f"Multiple dataset schema errors: {exc}"
        ) from exc

    # 2. Record-level validation

    checks = pd.DataFrame(index=df.index)

    checks["missing_transaction_id"] = (
        df["transaction_id"].isna()
    )

    checks["missing_customer_id"] = (
        df["customer_id"].isna()
    )

    checks["missing_amount"] = (
        df["amount"].isna()
    )

    checks["invalid_amount"] = (
        df["amount"].notna() & (df["amount"] <= 0)
    )

    checks["invalid_currency"] = (
        ~df["currency"].isin(ALLOWED_CURRENCIES)
    )

    checks["invalid_payment_status"] = (
        ~df["payment_status"].isin(ALLOWED_STATUSES)
    )

    checks["duplicate_transaction_id"] = (
        df["transaction_id"].duplicated(keep=False)
    )

    invalid_mask = checks.any(axis=1)

    valid_df = df.loc[~invalid_mask].copy()
    invalid_df = df.loc[invalid_mask].copy()

    # 3. Add rejection reasons

    invalid_df["validation_errors"] = checks.loc[
        invalid_mask
    ].apply(
        lambda row: ",".join(
            row.index[row].tolist()
        ),
        axis=1,
    )

    # 4. Save output

    VALID_FILE.parent.mkdir(parents=True, exist_ok=True)
    INVALID_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    valid_df.to_csv(VALID_FILE, index=False)
    invalid_df.to_csv(INVALID_FILE, index=False)

    # 5. Generate report

    report = {
        "total_records": len(df),
        "valid_records": len(valid_df),
        "invalid_records": len(invalid_df),
        "validation_status": (
            "PASSED" if len(invalid_df) == 0 else "PARTIAL_FAILURE"
        ),
    }

    REPORT_FILE.write_text(
        json.dumps(report, indent=4)
    )

    print(json.dumps(report, indent=4))


if __name__ == "__main__":
    validate_dataset()
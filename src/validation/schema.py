import pandera.pandas as pa


TRANSACTION_SCHEMA = pa.DataFrameSchema(
    {
        "transaction_id": pa.Column(str, nullable=False),
        "customer_id": pa.Column(str, nullable=False),
        "amount": pa.Column(float, nullable=True),
        "currency": pa.Column(str, nullable=False),
        "payment_status": pa.Column(str, nullable=False),
    },
    strict=True,
    coerce=True,
)
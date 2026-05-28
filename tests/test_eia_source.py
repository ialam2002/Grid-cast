from gridcast.data.sources.eia import parse_eia_region_payload


def test_parse_eia_region_payload_maps_fields() -> None:
    payload = {
        "response": {
            "data": [
                {"period": "2026-01-01T00", "respondent": "CISO", "value": "22123"},
                {"period": "2026-01-01T01", "respondent": "CISO", "value": "21998"},
            ]
        }
    }

    df = parse_eia_region_payload(payload)

    assert list(df.columns) == ["timestamp_utc", "region", "demand_mw"]
    assert len(df) == 2
    assert df["region"].iloc[0] == "CISO"
    assert float(df["demand_mw"].iloc[0]) == 22123.0


"""Sample responses in each source's real format (formats verified 18 Nov 2026 where noted)."""

FRED_CPI = {
    "observations": [
        {"date": "2026-08-01", "value": "2.9"},
        {"date": "2026-09-01", "value": "3.0"},
        {"date": "2026-10-01", "value": "."},
    ]
}
FRED_ERROR = {"error_code": 400, "error_message": "Bad Request. The series does not exist."}

# Verified format
TREASURY_CSV = (
    'Date,"1 Mo","1.5 Month","2 Mo","3 Mo","4 Mo","6 Mo","1 Yr","2 Yr","3 Yr","5 Yr","7 Yr",'
    '"10 Yr","20 Yr","30 Yr"\n'
    "11/17/2026,4.09,4.24,4.26,4.33,4.32,4.41,4.60,4.80,4.84,4.90,4.99,5.10,5.50,5.46\n"
    "11/16/2026,4.10,4.19,4.27,4.34,4.33,4.42,4.62,4.83,4.87,4.93,5.01,5.12,5.51,5.46\n"
)

ECB_CSV = (
    "KEY,FREQ,REF_AREA,ADJUSTMENT,ICP_ITEM,STS_INSTITUTION,ICP_SUFFIX,TIME_PERIOD,OBS_VALUE\n"
    "ICP.M.U2.N.000000.4.ANR,M,U2,N,000000,4,ANR,2026-09,2.1\n"
    "ICP.M.U2.N.000000.4.ANR,M,U2,N,000000,4,ANR,2026-10,2.2\n"
)

# Verified format
BOE_CSV = "DATE,IUDBEDR,IUDMNZC\n01 Oct 2026,3.75,5.424\n02 Oct 2026,3.75,5.354\n"

# Verified element format
ONS_JSON = {
    "years": [],
    "quarters": [],
    "months": [
        {"date": "2025 OCT", "value": "3.6", "label": "2025 OCT", "year": "2025",
         "month": "October", "quarter": "", "sourceDataset": "MM23"},
        {"date": "2026 JAN", "value": "3.0", "label": "2026 JAN", "year": "2026",
         "month": "January", "quarter": "", "sourceDataset": "MM23",
         "updateDate": "2026-02-18T00:00:00.000Z"},
    ],
}

# Verified format (current-month file, including its title row and footer)
MOF_CSV = (
    "Interest Rate (November 2026),,,,,,,,,,,,,,,(Unit : %)\n"
    "Date,1Y,2Y,3Y,4Y,5Y,6Y,7Y,8Y,9Y,10Y,15Y,20Y,25Y,30Y,40Y\n"
    "2026/11/2,1.671,1.88,1.982,2.136,2.243,2.326,2.429,2.569,2.692,2.817,3.362,3.669,3.972,3.94,3.96\n"
    "2026/11/4,1.676,1.891,1.997,2.159,2.269,2.358,2.465,2.603,2.728,2.855,3.393,3.693,4.004,3.979,3.99\n"
    ",,,,,,,,,,,,,,,\n"
    "  If you cannot download the latest csv data, please clear the browser's cache."
    ",,,,,,,,,,,,,,,\n"
)
MOF_HISTORY_CSV = (
    "Interest Rate,,,,,,,,,,,,,,,(Unit : %)\n"
    "Date,1Y,2Y,3Y,4Y,5Y,6Y,7Y,8Y,9Y,10Y,15Y,20Y,25Y,30Y,40Y\n"
    "R8.10.30,1.6,1.85,1.95,2.1,2.2,2.3,2.4,2.5,2.6,2.79,3.3,3.6,3.9,3.9,3.95\n"
)

BOJ_JSON = {
    "STATUS": 200,
    "MESSAGEID": "M181000I",
    "MESSAGE": "Successfully completed",
    "RESULTSET": [{
        "SERIES_CODE": "STRDCLUCON",
        "NAME_OF_TIME_SERIES": "Call Rate, Uncollateralized Overnight/Average",
        "VALUES": {"SURVEY_DATES": [20261104, 20261105, 20261106],
                   "VALUES": [0.727, 0.728, None]},
    }],
}

# Verified values/codes
ECOS_BASERATE = {
    "StatisticSearch": {
        "list_total_count": 3,
        "row": [
            {"STAT_CODE": "722Y001", "ITEM_CODE1": "0101000", "TIME": "202501", "DATA_VALUE": "3"},
            {"STAT_CODE": "722Y001", "ITEM_CODE1": "0101000", "TIME": "202502",
             "DATA_VALUE": "2.75"},
            {"STAT_CODE": "722Y001", "ITEM_CODE1": "0101000", "TIME": "202503",
             "DATA_VALUE": "2.75"},
        ],
    }
}
ECOS_CPI = {
    "StatisticSearch": {
        "list_total_count": 4,
        "row": [
            {"TIME": "202501", "DATA_VALUE": "115.0"},
            {"TIME": "202502", "DATA_VALUE": "115.5"},
            {"TIME": "202601", "DATA_VALUE": "118.03"},
            {"TIME": "202602", "DATA_VALUE": "118.4"},
        ],
    }
}
ECOS_NO_DATA = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "No data."}}
ECOS_BAD_KEY = {"RESULT": {"CODE": "INFO-100", "MESSAGE": "Invalid authentication key."}}
